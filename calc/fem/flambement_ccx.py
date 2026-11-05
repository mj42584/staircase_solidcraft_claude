"""Flambement : barres isolées en CalculiX (*BUCKLE, poutres B32R à section tube développée) et facteur critique de
l'ossature du palier par la méthode de Horne (EN 1993-1-1 §5.2.1 (4)) sur le modèle CalculiX et sur PyNite.

Barres : diagonale 40 × 40 × 3 articulée aux deux bouts (L du modèle) ; pied 100 × 100 × 5 encastré au sol, tête tenue
latéralement (palier contreventé), tête articulée ou encastrée. Comparées à l'Euler de flambement() (predim.py), qui
prend L_cr = L pour les deux.
Lancer après global_ccx.py (relit ses résultats) : ~/.venvs/escalier/bin/python calc/fem/flambement_ccx.py
"""
import os
import subprocess
import sys
from math import pi, sqrt

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import portique as p  # noqa: E402
from ccx_modele import CCX, DOSSIER, lire_dat  # noqa: E402


def flambe(nom, L, cote, ep, tete):
    """Charge critique (N) d'une barre tube carré verticale de longueur L ; tete : 'articulée' ou 'encastrée'
    (déplacements latéraux bloqués en tête dans les deux cas) ; pied : 'encastré' ou 'articulé' selon nom."""
    n = 40
    lignes = ["*NODE, NSET=NALL"] + [f"{i + 1},0,0,{L * i / (2 * n):.4f}" for i in range(2 * n + 1)]
    lignes += ["*ELEMENT,TYPE=B32R,ELSET=B"] + [f"{k + 1},{2 * k + 1},{2 * k + 2},{2 * k + 3}" for k in range(n)]
    lignes += ["*MATERIAL,NAME=ACIER", "*ELASTIC", "210000,0.3",
               "*BEAM SECTION,ELSET=B,MATERIAL=ACIER,SECTION=BOX", f"{cote},{cote},{ep},{ep},{ep},{ep}", "1,0,0",
               "*BOUNDARY"]
    pied_encastre = nom.startswith("pied")
    lignes += ["1,1,6" if pied_encastre else "1,1,3\n1,6,6"]  # 6 : rotation propre bloquée
    haut = 2 * n + 1
    lignes += [f"{haut},1,2"] + ([f"{haut},4,5"] if tete == "encastrée" else [])
    lignes += ["*STEP", "*BUCKLE", "1", "*CLOAD", f"{haut},3,-1.0", "*END STEP"]
    with open(os.path.join(DOSSIER, nom + ".inp"), "w") as f:
        f.write("\n".join(lignes) + "\n")
    r = subprocess.run(CCX + ["-i", nom], cwd=DOSSIER, capture_output=True, text=True)
    if "ERROR" in r.stdout:
        raise RuntimeError(r.stdout[-2000:])
    txt = open(os.path.join(DOSSIER, nom + ".dat")).read()
    i = txt.index("B U C K L I N G   F A C T O R")
    return float(txt[i:].split("\n")[5].split()[1])


def euler(L, cote, ep):
    I = (cote**4 - (cote - 2 * ep) ** 4) / 12
    return pi**2 * p.E_acier * I / L**2


L_d = sqrt((2 * (p.Y_c - p.poteau_cote - p.gousset_trou_l)) ** 2
           + (p.Z_c - p.limon_h / 2 - p.platine_pied_ep - p.gousset_jeu_tete - p.gousset_h - p.platine_pied_ep) ** 2)
H = p.Z_c
print(f"{'Barre':42} {'Ncr CalculiX':>13} {'Ncr Euler L_cr = L':>19}  rapport")
for nom, L, c, t, tete in (("diagonale", L_d, p.diag_cote, p.diag_ep, "articulée"),
                           ("pied_tete_articulee", H, p.poteau_cote, p.poteau_ep, "articulée"),
                           ("pied_tete_encastree", H, p.poteau_cote, p.poteau_ep, "encastrée")):
    Nc, Ne = flambe(nom, L, c, t, tete), euler(L, c, t)
    print(f"{nom + f' (L = {L:.0f})':42} {Nc / 1e3:10.1f} kN {Ne / 1e3:16.1f} kN  {Nc / Ne:6.2f}"
          f"  → L_cr = {sqrt(Ne / Nc):.2f} L")

# --- Horne : alpha_cr = (H_Ed / V_Ed) (h / delta_H) ; H_Ed = forces des défauts aux 4 angles (cas HX, HY), V_Ed =
# charge verticale ELU (1,35 G + 1,5 Q) reprise par les pieds, delta_H = déplacement horizontal du palier sous H_Ed
import json  # noqa: E402

print("\nFacteur critique de l'ossature du palier (Horne), alpha_cr ≥ 10 : calcul au premier ordre suffisant")
for tete in (False, True):
    nom = "global_rigide" if tete else "global_articule"
    mp, _, coins = p.construire(tete)
    for d, cas, ddl in (("X", "HX", "DX"), ("Y", "HY", "DZ")):
        mp.add_load_combo("h" + d, {cas: 1})
    mp.add_load_combo("v", {"G": 1.35, "Q": 1.5})
    mp.analyze(check_statics=False)
    V = sum(mp.nodes["S" + n].RxnFY["v"] for n in coins)
    H4 = sum(abs(P) for n in coins for (dd, P, c) in mp.nodes[n].NodeLoads if c == "HX")
    info = json.load(open(os.path.join(DOSSIER, nom + ".json")))
    res = lire_dat(os.path.join(DOSSIER, nom + ".dat"))
    i_ = {c: k + 1 for k, c in enumerate(info["cas"])}
    V_fe = sum(-(1.35 * res[i_["G"]]["RF"][int(b)][2] + 1.5 * sum(res[i_[q]]["RF"][int(b)][2] for q in ("QV1", "QV2", "QP")))
               for b in info["bases"].values())  # composante Z des réactions U1 imprimée de signe opposé (global_ccx.py)
    for d, cas, ddl, j in (("X", "HX", "DX", 0), ("Y", "HY", "DZ", 1)):
        delta_p = max(abs(getattr(mp.nodes[n], ddl)["h" + d]) for n in coins)
        delta_f = max(abs(res[i_[cas]]["U"][int(c)][j]) for c in info["coins"].values())
        a_p = H4 / V * p.Z_c / delta_p
        a_f = 4 * info["H"] / V_fe * p.Z_c / delta_f
        print(f"  tête {'rigide' if tete else 'articulée'}, en {d} : PyNite {a_p:6.0f} (V {V / 1e3:.1f} kN, delta {delta_p:.4f} mm)"
              f"   CalculiX {a_f:6.0f} (V {V_fe / 1e3:.1f} kN, delta {delta_f:.4f} mm)")

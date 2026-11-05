"""Contre-calcul du modèle en barres (portique.py) par éléments finis CalculiX, indépendant de PyNite.

Limons et cadre du palier en volumes (UPE 220 sans congés, briques C3D20R) : torsion, gauchissement et excentricité
des charges sont donc réels, alors que PyNite les ignore ou les traite à part. Pieds, diagonales et marches en poutres.
Géométrie des axes, appuis, charges et combinaisons repris de portique.py / predim.py, sauf :
- les marches sont modélisées (poutres de chêne liées aux limons par un ressort K_VIS, comme marches_traverses()) et
  portent leur poids et la charge d'exploitation ; elles s'appuient sur le dos de l'âme (cornière), pas sur l'axe ;
- la poussée sur les mains courantes est appliquée sur l'aile haute avec son couple (hauteur de la main courante) ;
- les limons sont liés à l'âme de la poutre avant par une articulation (forces et torsion transmises, pas la flexion)
  au droit des boulons, sans barre d'excentricité : elle vient de la géométrie.
Lancer : ~/.venvs/escalier/bin/python calc/fem/global_ccx.py [--tete-rigide]  (CalculiX du Flatpak FreeCAD, quelques minutes)
"""
import os
import sys
from math import cos, sin, sqrt, tan

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import portique as p  # noqa: E402
from ccx_modele import DOSSIER, Modele, Upe, lire_dat, lire_frd, unit, von_mises  # noqa: E402

TETE_RIGIDE = "--tete-rigide" in sys.argv
NOM = "global_rigide" if TETE_RIGIDE else "global_articule"
h, b, tw, tf = p.limon_h, p.limon_b, p.limon_tw, p.limon_tf
X_r, X_b, X_a, Z_c, Y_c, X_0, dz = p.X_r, p.X_b, p.X_a, p.Z_c, p.Y_c, p.X_0, p.dz
hm, g, ang = p.hauteur_marche, p.giron, p.angle
CAS = ["G", "QV1", "QV2", "QP", "GCX", "GCY", "HX", "HY", "GCY0"]  # GCY0 : poussée sans son couple, comme portique.py

m = Modele()
upe = {}


def n_haut(u):
    return np.array([-u[2], 0, u[0]]) if u[0] > 0 else np.array([u[2], 0, -u[0]])


# --- Limons : axe de portique.py (centre de gravité), section à partir du dos de l'âme
axes = {"V1": (np.array([X_0, 0, 0]), np.array([X_r + p.excentricite, 0, Z_c])),
        "V2": (np.array([X_r + p.excentricite, 0, Z_c]), np.array([X_a, 0, p.hauteur_totale - dz]))}
for v, (ya, yb) in p.y_limons.items():
    A, B = axes[v]
    u = unit(B - A)
    for k, y in enumerate((ya, yb)):
        ext = abs(y) > p.jour / 2 + p.emmarchement / 2
        w = np.array([0, np.sign(y) if ext else -np.sign(y), 0])  # ailes à l'opposé des marches
        o = A + np.array([0, y - w[1] * b / 2, 0])                  # dos de l'âme
        s_debut = 0.0 if v == "V1" else (X_r - p.platine_ep - A[0]) / u[0]
        s_fin = ((X_r - p.platine_ep if v == "V1" else X_a + p.platine_ep) - A[0]) / u[0]
        upe[f"L{v}{k}"] = Upe(m, f"L{v}{k}", o, u, n_haut(u), w, s_debut, s_fin, h, b, tw, tf)

# --- Cadre : âmes à l'extérieur, ailes vers l'intérieur, chaque poutre jusqu'aux angles extérieurs
for nom, o, u, w, L in (("PA", (X_r, -Y_c, Z_c), (0, 1, 0), (1, 0, 0), 2 * Y_c),
                        ("PB", (X_b, -Y_c, Z_c), (0, 1, 0), (-1, 0, 0), 2 * Y_c),
                        ("PL1", (X_r, -Y_c, Z_c), (1, 0, 0), (0, 1, 0), p.palier_profondeur),
                        ("PL2", (X_r, Y_c, Z_c), (1, 0, 0), (0, -1, 0), p.palier_profondeur)):
    upe[nom] = Upe(m, nom, o, u, (0, 0, 1), w, 0, L, h, b, tw, tf)

# Angles soudés : les deux bouts de poutre rigides ensemble, nœud de l'angle comme portique.py
coins = {}
for nom, (x, y), (a, sa), (c, sc) in (("A0", (X_r, -Y_c), ("PA", 0), ("PL1", 0)),
                                      ("A5", (X_r, Y_c), ("PA", 2 * Y_c), ("PL2", 0)),
                                      ("B0", (X_b, -Y_c), ("PB", 0), ("PL1", p.palier_profondeur)),
                                      ("B1", (X_b, Y_c), ("PB", 2 * Y_c), ("PL2", p.palier_profondeur))):
    coins[nom] = (x, y) + m.rigide(upe[a].section(sa) + upe[c].section(sc), (x, y, Z_c))

# --- Limons sur la poutre avant : platine rigide au bout du limon, articulée au droit des 2 boulons dans l'âme
for v in ("V1", "V2"):
    for k, y in enumerate(p.y_limons[v]):
        L_ = upe[f"L{v}{k}"]
        s_bout = L_.s[-1] if v == "V1" else L_.s[0]
        rl, ql = m.rigide(L_.section(s_bout), (X_r, y, Z_c))
        pa = upe["PA"]
        patch = pa.zone(lambda s, yy, z, y=y: abs(s - (y + Y_c)) <= 30 and abs(z) <= 70 and yy <= tw + 1e-6)
        rp, qp = m.rigide(patch, (X_r, y, Z_c))
        m.lier(rl, rp)
        m.lier_rotation(ql, 1, qp, 1, L_.u)

# --- Appuis des limons : pied de V1 articulé, haut de V2 articulé avec la rotation autour de X bloquée
sorties_appuis = {}
for k, y in enumerate(p.y_limons["V1"]):
    r, q = m.rigide(upe[f"LV1{k}"].section(0), (X_0, y, 0))
    m.appuis.append((r, 1, 3))
    sorties_appuis[f"LV1{k}"] = r
for k, y in enumerate(p.y_limons["V2"]):
    L_ = upe[f"LV2{k}"]
    r, q = m.rigide(L_.section(L_.s[-1]), (X_a, y, p.hauteur_totale - dz))
    m.appuis += [(r, 1, 3), (q, 1, 1)]
    sorties_appuis[f"LV2{k}"] = r

# --- Pieds encastrés au sol, goussets rigides, diagonales articulées
tube = (p.tube_A, p.tube_I, p.tube_I, (1, 0, 0), "ACIER")
rigide = (1e6, 1e10, 1e10, (1, 0, 0), "ACIER")
z_bas = p.platine_pied_ep + p.gousset_h / 2
z_haut = Z_c - h / 2 - p.platine_pied_ep - p.gousset_jeu_tete - p.gousset_h / 2
pieds, bases = {}, {}
for nom, (x, y, ref, rot) in coins.items():
    ns = m.poutre(f"T{nom}", (x, y, 0), (x, y, z_bas), 2, tube)
    ns += m.poutre(f"T{nom}", ns[-1], (x, y, z_haut), 20, tube)[1:]
    ns += m.poutre(f"T{nom}", ns[-1], (x, y, Z_c), 2, tube)[1:]
    m.appuis.append((ns[0], 1, 6))
    m.attacher(ns[-1], ref, rot, rotations=(4, 5, 6) if TETE_RIGIDE else (6,))  # articulée : torsion seule
    pieds[nom], bases[nom] = ns, ns[0]
d_g = p.poteau_cote + p.gousset_trou_l
diag = (p.diag_A, p.diag_I, p.diag_I, (1, 0, 0), "ACIER")
diagonales = {}
for nom, bas, haut in (("DA", "A0", "A5"), ("DB", "B1", "B0")):
    bouts = []
    for coin, z, i in ((bas, z_bas, 2), (haut, z_haut, 22)):
        x, y = coins[coin][:2]
        gn = m.poutre(f"G{nom}", pieds[coin][i], (x, y - d_g * np.sign(y), z), 1, rigide)[-1]
        bouts.append(gn)
    pa_, pb_ = m.nodes[bouts[0] - 1], m.nodes[bouts[1] - 1]
    ns = m.poutre(nom, tuple(pa_), tuple(pb_), 10, diag)
    diagonales[nom] = (ns, np.linalg.norm(pb_ - pa_))
    for e, gn in ((ns[0], bouts[0]), (ns[-1], bouts[1])):
        m.lier(e, gn)
        m.lier_rotation(e, 4, gn, 4, pb_ - pa_)

# --- Marches : poutre de chêne entre les dos des âmes, à mi-épaisseur, liée par un ressort K_VIS (portique.py)
lc = p.liaison_lc
I_l = p.K_VIS * lc / p.E_acier
liaison = (1e6, I_l, I_l, (0, 0, 1), "ACIER")
marche = (g * p.marche_epaisseur, g * p.marche_epaisseur**3 / 12, p.marche_epaisseur * g**3 / 12, (0, 0, 1), "CHENE")
marches = []
for v, xs, tops in (("V1", [(j + 0.5) * g for j in range(p.nb_volee1 - 1)], [(j + 1) * hm for j in range(p.nb_volee1 - 1)]),
                    ("V2", [X_r - (j + 0.5) * g for j in range(p.nb_volee2)], [(p.nb_volee1 + j) * hm for j in range(p.nb_volee2)])):
    for j, (x, zt) in enumerate(zip(xs, tops)):
        bouts = []
        for k in (0, 1):
            L_ = upe[f"L{v}{k}"]
            y_dos = L_.o[1]
            zc = zt - p.marche_epaisseur  # dessous de la marche = dessus de la cornière
            patch = [n for n in L_.zone(lambda s, yy, z: yy < 1e-6)
                     if abs(m.nodes[n - 1][0] - x) <= 100 and zc - 50 - 17 <= m.nodes[n - 1][2] <= zc + 17]
            assert len(patch) >= 6, (v, j, k, len(patch))
            sens = -L_.w[1]  # vers la marche
            r, q = m.rigide(patch, (x, y_dos, zt - p.marche_epaisseur / 2))
            m1 = m.noeud((x, y_dos, zt - p.marche_epaisseur / 2))
            m.attacher(m1, r, q)
            m2 = m.poutre(f"R{v}{j}_{k}", m1, (x, y_dos + sens * lc, zt - p.marche_epaisseur / 2), 1, liaison)[-1]
            bouts.append(m2)
        ns = m.poutre(f"M{v}{j}", bouts[0], bouts[1], 4, marche)
        marches.append((v, j, ns))

# --- Charges (N, mm), comme portique.py
G_tot, Q_tot = 0.0, 0.0


def nodal(cas, ns, F, d):
    """F (N) réparti sur les nœuds d'une poutre (bouts à moitié)."""
    poids = np.array([0.5] + [1.0] * (len(ns) - 2) + [0.5])
    for n, c in zip(ns, poids / poids.sum()):
        m.charge(cas, n, d, F * c)


for v, j, ns in marches:
    G_m = p.marche_g if hasattr(p, "marche_g") else p.g_chene * g * p.marche_epaisseur * p.emmarchement + p.equerres_g
    nodal("G", ns, -G_m, 3)
    nodal(f"Q{v}", ns, -p.q_k * g * p.emmarchement, 3)
    G_tot += G_m
    Q_tot += p.q_k * g * p.emmarchement

for nom, ns in pieds.items():  # poids propre des pieds et des diagonales, comme portique.py
    nodal("G", ns, -p.tube_A * p.g_acier * Z_c, 3)
    G_tot += p.tube_A * p.g_acier * Z_c
for nom, (ns, L_d) in diagonales.items():
    nodal("G", ns, -p.diag_A * p.g_acier * L_d, 3)
    G_tot += p.diag_A * p.g_acier * L_d

ame = lambda s, y, z: y <= tw + 1e-6
dessus = lambda s, y, z: abs(z - h / 2) < 1e-6
for nom, L_ in upe.items():
    longueur = L_.s[-1] - L_.s[0]
    w_g = p.upe_g + (p.g_gc if nom != "PA" else 0.0)
    L_.ligne("G", ame, (0, 0, -w_g))
    G_tot += w_g * longueur
    if nom in ("PA", "PB"):
        w_pl, w_q = p.g_chene * p.palier_ep * p.palier_profondeur / 2, p.q_k * p.palier_profondeur / 2
        L_.ligne("G", dessus, (0, 0, -w_pl))
        L_.ligne("QP", dessus, (0, 0, -w_q))
        G_tot += w_pl * longueur
        Q_tot += w_q * longueur

# Poussée des mains courantes : force à mi-largeur de l'aile haute + couple (bras jusqu'à l'axe de la main courante)
# par deux lignes verticales opposées sur l'aile, aux nœuds y' encadrant le milieu
ys_aile = sorted({round(y, 4) for n, (s, y, z) in upe["PA"].loc.items() if abs(z - h / 2) < 1e-6 and y > tw})


def poussee(L_, cas, q, direction, bras, couple=True):
    y1, y2 = ys_aile[len(ys_aile) // 2 - 2], ys_aile[len(ys_aile) // 2 + 2]
    L_.ligne(cas, lambda s, y, z: abs(z - h / 2) < 1e-6 and (abs(y - y1) < 1e-3 or abs(y - y2) < 1e-3), q * np.asarray(direction))
    if not couple:
        return
    F = q * bras / (y2 - y1)
    # couple r × F de la poussée à la hauteur bras (r vertical) : M = bras e_z × direction ; deux lignes verticales
    # opposées sur l'aile, aux abscisses y1 < y2 le long de w : M = F (y2 - y1) w × e_z → F en y2 du signe de -w · dir
    sgn = -np.sign(np.dot(L_.w, direction))
    L_.ligne(cas, lambda s, y, z: abs(z - h / 2) < 1e-6 and abs(y - y2) < 1e-3, (0, 0, sgn * F))
    L_.ligne(cas, lambda s, y, z: abs(z - h / 2) < 1e-6 and abs(y - y1) < 1e-3, (0, 0, -sgn * F))


bras_volee = p.mc_h + p.limon_descente   # dessus du limon → axe de la main courante (potelets, predim.py)
bras_palier = p.palier_ep + p.mc_palier_h
for v in ("V1", "V2"):
    for k in (0, 1):
        poussee(upe[f"L{v}{k}"], "GCY", p.q_gc, (0, 1, 0), bras_volee)
        poussee(upe[f"L{v}{k}"], "GCY0", p.q_gc, (0, 1, 0), bras_volee, couple=False)
for nom in ("PL1", "PL2"):
    poussee(upe[nom], "GCY", p.q_gc, (0, 1, 0), bras_palier)
    poussee(upe[nom], "GCY0", p.q_gc, (0, 1, 0), bras_palier, couple=False)
poussee(upe["PB"], "GCX", p.q_gc, (1, 0, 0), bras_palier)

# Défauts de verticalité aux 4 angles (portique.py)
alpha_h = min(1.0, max(2 / 3, 2 / sqrt(Z_c / 1000)))
phi = 1 / 200 * alpha_h * sqrt(0.5 * (1 + 1 / 4))
H = phi * (1.35 * G_tot + 1.5 * Q_tot) / 4
for nom, (x, y, ref, rot) in coins.items():
    m.charge("HX", ref, 1, H)
    m.charge("HY", ref, 2, H)
r_els = (G_tot + Q_tot) / (1.35 * G_tot + 1.5 * Q_tot)

m.sorties["coins"] = [c[2] for c in coins.values()]
m.sorties["appuis"] = list(bases.values()) + list(sorties_appuis.values())
m.ecrire(NOM, CAS)
import json  # noqa: E402
json.dump({"coins": {k: c[2] for k, c in coins.items()}, "bases": bases, "H": H, "G": G_tot, "Q": Q_tot, "cas": CAS},
          open(os.path.join(DOSSIER, NOM + ".json"), "w"))
print(f"{len(m.nodes)} nœuds, {sum(len(c) for _, c in m.elsets.values())} éléments ; G = {G_tot / 1e3:.1f} kN, Q = {Q_tot / 1e3:.1f} kN")
res = lire_dat(os.path.join(DOSSIER, NOM + ".dat")) if "--relire" in sys.argv else m.lancer(NOM)
ids, xyz, S, _ = lire_frd(os.path.join(DOSSIER, NOM + ".frd"))
cas_i = {c: i + 1 for i, c in enumerate(CAS)}

# --- Combinaisons (portique.py)
combos = {}
for d in ("X", "Y"):
    for s, sens in ((1, ""), (-1, "-")):
        Q = {"QV1": 1, "QV2": 1, "QP": 1}
        combos[f"ELU_{d}{sens}"] = {"G": 1.35, **{q: 1.5 for q in Q}, f"H{d}": s}
        combos[f"ELS_{d}{sens}"] = {"G": 1.0, **Q, f"H{d}": s * r_els}
        combos[f"ELU_GC{d}{sens}"] = {"G": 1.35, f"GC{d}": 1.5 * s, **{q: 1.05 for q in Q}, f"H{d}": s}
        combos[f"ELU_GC{d}{sens}_sou"] = {"G": 1.0, f"GC{d}": 1.5 * s, f"H{d}": s}
        combos[f"ELS_GC{d}{sens}"] = {"G": 1.0, f"GC{d}": s, **{q: 0.7 for q in Q}, f"H{d}": s * r_els}
        for seul in ("V1", "V2"):
            autre = "V2" if seul == "V1" else "V1"
            combos[f"ELU_{d}{sens}_{seul}seul"] = {"G": 1.35, f"Q{seul}": 1.5, "QP": 1.5, f"H{d}": s}
            combos[f"ELS_{d}{sens}_{seul}seul"] = {"G": 1.0, f"Q{seul}": 1.0, "QP": 1.0, f"H{d}": s * r_els}


def comb(f, c):
    return sum(k * f(cas_i[cas]) for cas, k in combos[c].items())


elu = [c for c in combos if c.startswith("ELU")]
els = [c for c in combos if c.startswith("ELS")]
U = lambda n: (lambda i: np.array(res[i]["U"][n][:3]))
# CalculiX 2.23 imprime la réaction d'un appui de poutre U1 avec la composante le long de la poutre de signe opposé
# (essai : poteau vertical chargé de -1000 N en Z et +100 N en Y → RF = (0, -100, -1000)) ; pieds verticaux : Z inversé
signe_rf = {n: np.array([1.0, 1.0, -1.0]) for n in bases.values()}
RF = lambda n: (lambda i: signe_rf.get(n, 1.0) * np.array(res[i]["RF"][n][:3]))

out = {}
out["Palier, en long (X), dépl. ELS (mm)"] = max(abs(comb(U(c[2]), k)[0]) for c in coins.values() for k in els)
out["Palier, en travers (Y), dépl. ELS (mm)"] = max(abs(comb(U(c[2]), k)[1]) for c in coins.values() for k in els)


def efforts(es):
    """Efforts de section des poutres U1 d'un elset, par pas : tableau (points, 6) : N, M, M, V, V, T."""
    return lambda i: np.array([v for _, _, v in res[i]["S"][es]])


for nom in ("DA", "DB"):
    Ns = [comb(efforts(nom), k)[:, 0] for k in elu]
    out[f"Diagonale {nom} compression ELU (kN)"] = -min(x.min() for x in Ns) / 1e3
    out[f"Diagonale {nom} traction ELU (kN)"] = max(x.max() for x in Ns) / 1e3
taux = 0.0
N_b = p.flambement(1, Z_c, p.tube_A, p.tube_I)
for nom in coins:
    for k in elu:
        e = comb(efforts(f"T{nom}"), k)
        taux = max(taux, (-e[:, 0]).max() / N_b + np.hypot(e[:, 1], e[:, 2]).max() / (p.tube_W * p.fy))
out["Pieds N + M ELU (taux)"] = taux
out["Pied de poteau N maxi ELU (kN)"] = max(abs(comb(RF(n), k)[2]) for n in bases.values() for k in elu) / 1e3
out["Pied de poteau V maxi ELU (kN)"] = max(np.hypot(*comb(RF(n), k)[:2]) for n in bases.values() for k in elu) / 1e3
out["Soulèvement maxi pied de poteau ELU (kN)"] = max(0, -min(comb(RF(n), k)[2] for n in bases.values() for k in elu)) / 1e3
for v in ("V1", "V2"):
    ns = [sorties_appuis[f"L{v}{k}"] for k in (0, 1)]
    out[f"Appui limon {v} N maxi ELU (kN)"] = max(abs(comb(RF(n), k)[2]) for n in ns for k in elu) / 1e3
    out[f"Appui limon {v} V maxi ELU (kN)"] = max(np.hypot(*comb(RF(n), k)[:2]) for n in ns for k in elu) / 1e3

# Marches et liaisons (vis à bois) : moments maxi sous la poussée en travers seule (comme marches_traverses())
gcy = [c for c in elu if c.startswith("ELU_GCY")]
sig_m = 0.0
for v, j, ns in marches:
    for k in elu:
        e = comb(efforts(f"M{v}{j}"), k)
        sig_m = max(sig_m, (np.abs(e[:, 1]) / (g * p.marche_epaisseur**2 / 6) + np.abs(e[:, 2]) / (p.marche_epaisseur * g**2 / 6)).max())
out["Marches chêne, flexion ELU (MPa)"] = sig_m
M_l = max(np.hypot(*comb(efforts(f"R{v}{j}_{k_}"), k)[:, 1:3].T).max() for v, j, _ in marches for k_ in (0, 1) for k in gcy)
out["Liaison marche-cornière, moment ELU_GCY (kN·m)"] = M_l / 1e6
out["Vis à bois la plus tendue (kN)"] = M_l * max(p.vis_x) / sum(x_**2 for x_ in p.vis_x) / 1e3

# Contraintes dans les UPE, hors zones d'attache (50 mm autour des corps rigides) : contrainte normale le long de la
# poutre (flexion + gauchissement), cisaillement dans le plan des parois (torsion + effort tranchant), von Mises
attaches = np.array([m.nodes[n - 1] for ns, _, _ in m.rigides for n in ns])
from scipy.spatial import cKDTree  # noqa: E402
loin = cKDTree(attaches).query(xyz, distance_upper_bound=50)[0] == np.inf
SC = {c: sum(k * S[cas_i[cas] - 1] for cas, k in combos[c].items()) for c in elu}


def tenseur(s6):
    xx, yy, zz, xy, yz, zx = s6.T
    return np.stack([np.stack([xx, xy, zx], -1), np.stack([xy, yy, yz], -1), np.stack([zx, yz, zz], -1)], -2)


upe_res = {}
for nom, L_ in upe.items():
    sel = np.array([n in L_.loc for n in ids]) & loin
    best = {"sig": (0, None, None), "tau": (0, None, None), "vm": (0, None, None)}
    for c in elu:
        T = tenseur(SC[c][sel])
        sig = np.abs(np.einsum("i,nij,j->n", L_.u, T, L_.u))
        tau = np.maximum(np.abs(np.einsum("i,nij,j->n", L_.u, T, L_.n)), np.abs(np.einsum("i,nij,j->n", L_.u, T, L_.w)))
        vm = von_mises(SC[c][sel])
        for k_, a in (("sig", sig), ("tau", tau), ("vm", vm)):
            i = int(a.argmax())
            if a[i] > best[k_][0]:
                best[k_] = (a[i], c, xyz[sel][i])
    upe_res[nom] = best
    for k_, lab in (("sig", "contrainte normale"), ("tau", "cisaillement"), ("vm", "von Mises")):
        v_, c, pt = best[k_]
        out[f"UPE {nom} {lab} ELU (MPa)"] = v_
        print(f"  {nom} {lab}: {v_:6.1f} MPa en {c} au point ({pt[0]:.0f}, {pt[1]:.0f}, {pt[2]:.0f})")

# --- Même grandeurs par PyNite (portique.py, assemblages.py), même tête des pieds
mp, pa_p, coins_p = p.construire(TETE_RIGIDE)
elu_p = [c for c in mp.load_combos if c.startswith("ELU")]
els_p = [c for c in mp.load_combos if c.startswith("ELS")]
nd, mb = mp.nodes, mp.members


def mmax(b_, axe, cs):
    return max(max(abs(mb[b_].max_moment(axe, c)), abs(mb[b_].min_moment(axe, c))) for c in cs)


def tmax(mod, b_, cs):
    return max(max(abs(mod.members[b_].max_torque(c)), abs(mod.members[b_].min_torque(c))) for c in cs)


ref = {
    "Palier, en long (X), dépl. ELS (mm)": max(abs(nd[n].DX[c]) for n in coins_p for c in els_p),
    "Palier, en travers (Y), dépl. ELS (mm)": max(abs(nd[n].DZ[c]) for n in coins_p for c in els_p),
    "Diagonales, compression ELU (kN)": max(mb[d].max_axial(c) for d in ("DA", "DB") for c in elu_p) / 1e3,
    "Diagonales, traction ELU (kN)": -min(mb[d].min_axial(c) for d in ("DA", "DB") for c in elu_p) / 1e3,
    "Pied de poteau, N maxi ELU (kN)": max(abs(nd["S" + n].RxnFY[c]) for n in coins_p for c in elu_p) / 1e3,
    "Pied de poteau, V maxi ELU (kN)": max(sqrt(nd["S" + n].RxnFX[c] ** 2 + nd["S" + n].RxnFZ[c] ** 2) for n in coins_p for c in elu_p) / 1e3,
    "Pied de poteau, soulèvement maxi ELU (kN)": max(0, -min(nd["S" + n].RxnFY[c] for n in coins_p for c in elu_p)) / 1e3,
}
for v in ("V1", "V2"):
    ns_ = [f"L{v}{k}s" for k in (0, 1)]
    ref[f"Appui limon {v}, N maxi ELU (kN)"] = max(abs(nd[n].RxnFY[c]) for n in ns_ for c in elu_p) / 1e3
    ref[f"Appui limon {v}, V maxi ELU (kN)"] = max(sqrt(nd[n].RxnFX[c] ** 2 + nd[n].RxnFZ[c] ** 2) for n in ns_ for c in elu_p) / 1e3
    ref[f"Limons {v}, contrainte normale ELU (MPa)"] = max(mmax(f"L{v}{k}", "Mz", [c]) / p.upe_W + mmax(f"L{v}{k}", "My", [c]) / p.upe_Wz
                                                         for k in (0, 1) for c in elu_p)
ref["Poutre avant, contrainte normale ELU (MPa)"] = max(mmax(b_, "Mz", [c]) / p.upe_W + mmax(b_, "My", [c]) / p.upe_Wz for b_ in pa_p for c in elu_p)
ref["Poutre avant, torsion ELU (MPa)"] = max(tmax(mp, b_, elu_p) for b_ in pa_p) * tf / p.upe_J
# torsion des limons, marches, vis : modèle avec les marches à K_VIS (marches_traverses), poussée en travers
mk, pa_k, _ = p.construire(k_marche=p.K_VIS)
gcy_p = [c for c in mk.load_combos if c.startswith("ELU_GCY")]
for v in ("V1", "V2"):
    ref[f"Limons {v}, torsion ELU (MPa)"] = max(tmax(mk, f"L{v}{k}", gcy_p) for k in (0, 1)) * tf / p.upe_J
mar = [b_ for b_ in mk.members if b_[0] == "M" and b_[-1].isdigit() and "_" not in b_]
lia = [b_ for b_ in mk.members if b_.endswith("r") and "_" in b_]
ref["Marches chêne, flexion ELU_GCY (MPa)"] = max(
    max(abs(mk.members[b_].max_moment("Mz", c)), abs(mk.members[b_].min_moment("Mz", c))) / (g * p.marche_epaisseur**2 / 6)
    + max(abs(mk.members[b_].max_moment("My", c)), abs(mk.members[b_].min_moment("My", c))) / (p.marche_epaisseur * g**2 / 6)
    for b_ in mar for c in gcy_p)
M_lp = max(max(abs(mk.members[b_].max_moment(a, c)), abs(mk.members[b_].min_moment(a, c))) for b_ in lia for a in ("My", "Mz") for c in gcy_p)
ref["Vis à bois la plus tendue ELU_GCY (kN)"] = M_lp * max(p.vis_x) / sum(x_**2 for x_ in p.vis_x) / 1e3
t_pal = 1.5 * p.q_gc * (h / 2 + p.palier_ep + p.mc_palier_h)   # assemblages.py, Saint-Venant seul
ref["Poutre arrière, torsion ELU (MPa)"] = t_pal * 2 * Y_c / 2 * tf / p.upe_J
ref["Poutres latérales, torsion ELU (MPa)"] = t_pal * p.palier_profondeur / 2 * tf / p.upe_J

fe = {
    "Palier, en long (X), dépl. ELS (mm)": out["Palier, en long (X), dépl. ELS (mm)"],
    "Palier, en travers (Y), dépl. ELS (mm)": out["Palier, en travers (Y), dépl. ELS (mm)"],
    "Diagonales, compression ELU (kN)": max(out["Diagonale DA compression ELU (kN)"], out["Diagonale DB compression ELU (kN)"]),
    "Diagonales, traction ELU (kN)": max(out["Diagonale DA traction ELU (kN)"], out["Diagonale DB traction ELU (kN)"]),
    "Pied de poteau, N maxi ELU (kN)": out["Pied de poteau N maxi ELU (kN)"],
    "Pied de poteau, V maxi ELU (kN)": out["Pied de poteau V maxi ELU (kN)"],
    "Pied de poteau, soulèvement maxi ELU (kN)": out["Soulèvement maxi pied de poteau ELU (kN)"],
    "Poutre avant, contrainte normale ELU (MPa)": upe_res["PA"]["sig"][0],
    "Poutre avant, torsion ELU (MPa)": upe_res["PA"]["tau"][0],
    "Marches chêne, flexion ELU_GCY (MPa)": out["Marches chêne, flexion ELU (MPa)"],
    "Vis à bois la plus tendue ELU_GCY (kN)": out["Vis à bois la plus tendue (kN)"],
    "Poutre arrière, torsion ELU (MPa)": upe_res["PB"]["tau"][0],
    "Poutres latérales, torsion ELU (MPa)": max(upe_res["PL1"]["tau"][0], upe_res["PL2"]["tau"][0]),
}
for v in ("V1", "V2"):
    fe[f"Appui limon {v}, N maxi ELU (kN)"] = out[f"Appui limon {v} N maxi ELU (kN)"]
    fe[f"Appui limon {v}, V maxi ELU (kN)"] = out[f"Appui limon {v} V maxi ELU (kN)"]
    fe[f"Limons {v}, contrainte normale ELU (MPa)"] = max(upe_res[f"L{v}{k}"]["sig"][0] for k in (0, 1))
    fe[f"Limons {v}, torsion ELU (MPa)"] = max(upe_res[f"L{v}{k}"]["tau"][0] for k in (0, 1))
fe["Pieds, N + M ELU (taux)"] = out["Pieds N + M ELU (taux)"]
taux_p = 0.0
N_bp = p.flambement(1, Z_c, p.tube_A, p.tube_I)
for n in coins_p:
    for c in elu_p:
        M_ = max(max(abs(mb["T" + n].max_moment(a, c)), abs(mb["T" + n].min_moment(a, c))) for a in ("My", "Mz"))
        taux_p = max(taux_p, mb["T" + n].max_axial(c) / N_bp + M_ / (p.tube_W * p.fy))
ref["Pieds, N + M ELU (taux)"] = taux_p

print(f"\n=== Tête des pieds {'rigide' if TETE_RIGIDE else 'articulée'} : PyNite / CalculiX ===")
print(f"{'Grandeur':52} {'PyNite':>9} {'CalculiX':>9}  Écart")
for k_ in ref:
    a, b2 = ref[k_], fe[k_]
    print(f"{k_:52} {a:9.2f} {b2:9.2f}  {(b2 - a) / a:+5.0%}" if a else f"{k_:52} {a:9.2f} {b2:9.2f}")
print("Torsion et contraintes CalculiX : maxima hors des 50 mm autour des liaisons ; von Mises maxi par poutre :",
      ", ".join(f"{k} {v['vm'][0]:.0f}" for k, v in upe_res.items()), "MPa")

# --- Contrôle : équilibre de chaque cas (réactions + charges = 0, en forces)
appuis_n = list(bases.values()) + list(sorties_appuis.values())
for c, i in cas_i.items():
    F = np.zeros(3)
    for (n, d), v in m.charges.get(c, {}).items():
        F[d - 1] += v
    R = sum(RF(n)(i) for n in appuis_n)
    # tolérance 1 % : CalculiX imprime aussi des efforts parasites de quelques N aux nœuds de référence liés
    assert np.allclose(F + R, 0, atol=1e-2 * max(1.0, np.abs(F).max())), (c, F, R)
print("Équilibre vérifié pour les", len(cas_i), "cas ; G : réactions verticales des pieds",
      [round(RF(n)(1)[2]) for n in bases.values()], "N")

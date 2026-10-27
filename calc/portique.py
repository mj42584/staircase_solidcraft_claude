"""Modèle en barres de l'escalier gab (PyNite) : stabilité, torsion de la poutre avant, efforts aux appuis.

Reprend les paramètres et hypothèses de calc/predim.py. Ordres de grandeur, pas une note de calcul.
Installer : pip install PyNiteFEA. Lancer : python3 calc/portique.py

Appuis : pieds et bas des limons V1 encastrés (platines chevillées dans la dalle) ; haut des limons V2
articulé (boulonné à la structure supérieure) ; limons articulés sur la poutre avant (platines boulonnées).
Les marches ne relient pas les limons entre eux dans le modèle (côté sécurité).
"""
from math import cos, isclose, sqrt, tan

from Pynite import FEModel3D

from predim import *  # noqa: F403 — paramètres, hypothèses, verif / afficher

# --- Sections. UPE : A et I fort du catalogue, axe faible et torsion calculés en parois minces sans congés
upe_A = 3390
A_aile, A_ame = limon_b * limon_tf, (limon_h - 2 * limon_tf) * limon_tw
x_g = (2 * A_aile * limon_b / 2 + A_ame * limon_tw / 2) / (2 * A_aile + A_ame)  # depuis le dos de l'âme
upe_Iz = (2 * (limon_tf * limon_b**3 / 12 + A_aile * (limon_b / 2 - x_g) ** 2)
          + (limon_h - 2 * limon_tf) * limon_tw**3 / 12 + A_ame * (x_g - limon_tw / 2) ** 2)
upe_Wz = upe_Iz / (limon_b - x_g)
upe_J = (2 * limon_b * limon_tf**3 + (limon_h - 2 * limon_tf) * limon_tw**3) / 3
# Centre de cisaillement, côté dos de l'âme ; les platines appuient sur le dos de l'âme
e_cc = (limon_b - limon_tw / 2) ** 2 * (limon_h - limon_tf) ** 2 * limon_tf / (4 * upe_I)
excentricite = e_cc - limon_tw / 2
c, t = poteau_cote, poteau_ep
tube_A, tube_I = c**2 - (c - 2 * t) ** 2, (c**4 - (c - 2 * t) ** 4) / 12
tube_J = (c - t) ** 3 * t  # tube carré mince : 4 Am² t / périmètre moyen
tube_W = tube_I / (c / 2)
g_acier = 7.85e-5  # N/mm³

# --- Géométrie (repère de CONCEPTION.md, Z vers le haut)
X_r = (nb_volee1 - 1) * giron                  # rive du palier = poutre avant
X_b = X_r + palier_profondeur                  # poutre arrière
X_a = X_r - nb_volee2 * giron                  # arrivée en haut de V2
Z_c = nb_volee1 * hauteur_marche - palier_ep - limon_h / 2   # axe du cadre
Y_c = jour / 2 + emmarchement + limon_b        # angles extérieurs du cadre
dz = limon_h / 2 / cos(angle)                  # axe du limon sous la ligne de nez
X_0 = (dz - hauteur_marche) / tan(angle)       # pied des limons V1 au sol
y_limons = {"V1": (-(jour / 2 + emmarchement + limon_b / 2), -(jour / 2 - limon_b / 2)),
            "V2": (jour / 2 - limon_b / 2, jour / 2 + emmarchement + limon_b / 2)}


def nouveau_modele():
    m = FEModel3D()
    m.add_material("acier", E_acier, E_acier / 2.6, 0.3, g_acier)
    # PyNite : local z = axe fort d'une barre non verticale quand Y est vertical
    m.add_section("UPE", upe_A, upe_Iz, upe_I, upe_J)
    m.add_section("tube", tube_A, tube_I, tube_I, tube_J)
    m.add_section("rigide", 1e6, 1e12, 1e12, 1e12)
    return m


def noeud(m, nom, x, y, z):
    return m.add_node(nom, x, z, y)  # PyNite veut Y vertical : (x, y, z) → (x, z, y)


def construire():
    m = nouveau_modele()
    tot = {"G": 0.0, "Q": 0.0}

    def charge(barre, cas, w):
        m.add_member_dist_load(barre, "FY", -w, -w, case=cas)
        tot[cas] += w * m.members[barre].L()

    # Cadre du palier : poutre avant coupée aux 4 limons, angles soudés (rigides)
    ys = [-Y_c, *y_limons["V1"], *y_limons["V2"], Y_c]
    for i, y in enumerate(ys):
        noeud(m, f"A{i}", X_r, y, Z_c)
    noeud(m, "B0", X_b, -Y_c, Z_c)
    noeud(m, "B1", X_b, Y_c, Z_c)
    poutres_avant = [m.add_member(f"PA{i}", f"A{i}", f"A{i + 1}", "acier", "UPE") for i in range(len(ys) - 1)]
    m.add_member("PB", "B0", "B1", "acier", "UPE")
    m.add_member("PL1", f"A0", "B0", "acier", "UPE")
    m.add_member("PL2", f"A{len(ys) - 1}", "B1", "acier", "UPE")
    w_G, w_Q = g_chene * palier_ep * palier_profondeur / 2 + upe_g, q_k * palier_profondeur / 2
    for b in (*poutres_avant, "PB"):
        charge(b, "G", w_G)
        charge(b, "Q", w_Q)
    for b in ("PL1", "PL2"):
        charge(b, "G", upe_g)

    # Pieds encastrés au sol
    coins = {"A0": (X_r, -Y_c), f"A{len(ys) - 1}": (X_r, Y_c), "B0": (X_b, -Y_c), "B1": (X_b, Y_c)}
    for haut, (x, y) in coins.items():
        noeud(m, f"S{haut}", x, y, 0)
        m.def_support(f"S{haut}", True, True, True, True, True, True)
        m.add_member(f"T{haut}", f"S{haut}", haut, "acier", "tube")
        charge(f"T{haut}", "G", tube_A * g_acier)

    # Limons : charges par mètre horizontal ramenées à la longueur inclinée
    marche_g = g_chene * giron * marche_epaisseur * emmarchement + equerres_g
    wl_G = marche_g / 2 / giron * cos(angle) + upe_g
    wl_Q = q_k * emmarchement / 2 * cos(angle)
    for volee, (y1, y2) in y_limons.items():
        for k, y in enumerate((y1, y2)):
            nom = f"L{volee}{k}"
            appui = f"A{ys.index(y)}"
            noeud(m, f"{nom}p", X_r + excentricite, y, Z_c)  # point d'appui de la platine sur l'âme
            m.add_member(f"{nom}e", appui, f"{nom}p", "acier", "rigide")
            if volee == "V1":
                noeud(m, f"{nom}s", X_0, y, 0)
                m.def_support(f"{nom}s", True, True, True, True, True, True)
                m.add_member(nom, f"{nom}s", f"{nom}p", "acier", "UPE")
                m.def_releases(nom, Ryj=True, Rzj=True)
            else:
                noeud(m, f"{nom}s", X_a, y, hauteur_totale - dz)
                m.def_support(f"{nom}s", True, True, True, True, False, False)  # RX bloqué : pas de rotation sur l'axe
                m.add_member(nom, f"{nom}p", f"{nom}s", "acier", "UPE")
                m.def_releases(nom, Ryi=True, Rzi=True)
            charge(nom, "G", wl_G)
            charge(nom, "Q", wl_Q)

    # Défauts de verticalité (EN 1993-1-1 §5.3.2) en forces horizontales aux 4 angles du palier
    alpha_h = min(1.0, max(2 / 3, 2 / sqrt(Z_c / 1000)))
    phi = 1 / 200 * alpha_h * sqrt(0.5 * (1 + 1 / 4))
    H = phi * (1.35 * tot["G"] + 1.5 * tot["Q"]) / 4
    for coin in coins:
        m.add_node_load(coin, "FX", H, case="HX")
        m.add_node_load(coin, "FZ", H, case="HY")
    r = (tot["G"] + tot["Q"]) / (1.35 * tot["G"] + 1.5 * tot["Q"])  # même défaut, sous charges ELS
    for d in ("X", "Y"):
        m.add_load_combo(f"ELU_{d}", {"G": 1.35, "Q": 1.5, f"H{d}": 1.0})
        m.add_load_combo(f"ELS_{d}", {"G": 1.0, "Q": 1.0, f"H{d}": r})
    # shortcut: Q partout en même temps, pas de chargement alterné d'une seule volée ; à ajouter si une vérif est limite
    m.analyze(check_statics=False)
    return m, poutres_avant, coins


def resultats(m, poutres_avant, coins):
    elu, els = ("ELU_X", "ELU_Y"), ("ELS_X", "ELS_Y")
    # Stabilité : déplacement horizontal du palier
    d = max(sqrt(m.nodes[n].DX[c] ** 2 + m.nodes[n].DZ[c] ** 2) for n in coins for c in els)
    verif("Palier (défauts de verticalité)", "dépl. horiz. ELS", d, Z_c / 300, "mm")

    # Poutre avant : flexion forte + faible, puis torsion de Saint-Venant
    sigma = max(abs(m.members[b].max_moment("Mz", c)) / upe_W + abs(m.members[b].max_moment("My", c)) / upe_Wz
                for b in poutres_avant for c in elu)
    sigma = max(sigma, max(abs(m.members[b].min_moment("Mz", c)) / upe_W + abs(m.members[b].min_moment("My", c)) / upe_Wz
                           for b in poutres_avant for c in elu))
    T = max(max(abs(m.members[b].max_torque(c)), abs(m.members[b].min_torque(c))) for b in poutres_avant for c in elu)
    verif("Poutre avant UPE 220", "flexion ELU", sigma, fy / gM0, "MPa")
    verif("Poutre avant UPE 220", "torsion ELU", T * limon_tf / upe_J, fy / sqrt(3) / gM0, "MPa")

    # Pieds : flambement (L_cr = 0,7 H, encastré en pied, tenu par le cadre en tête) + flexion
    H = Z_c
    N_b = flambement(1, 0.7 * H, tube_A, tube_I)
    taux = 0.0
    for p in (f"T{n}" for n in coins):
        for c in elu:
            N = -m.members[p].min_axial(c)
            M = max(abs(m.members[p].max_moment(a, c)) for a in ("My", "Mz"))
            M = max(M, max(abs(m.members[p].min_moment(a, c)) for a in ("My", "Mz")))
            taux = max(taux, N / N_b + M / (tube_W * fy / gM0))
    verif(f"Pieds tube {poteau_cote}×{poteau_ep}", "N + M ELU", taux, 1.0, "taux")

    # Limons V1 : flexion forte sous l'encastrement en pied
    sigma = max(max(abs(m.members[f"LV1{k}"].max_moment("Mz", c)), abs(m.members[f"LV1{k}"].min_moment("Mz", c))) / upe_W
                for k in (0, 1) for c in elu)
    verif("Limons V1 UPE 220", "flexion ELU", sigma, fy / gM0, "MPa")

    # Efforts aux appuis (ELU) pour chevilles et fixation de l'arrivée
    print("\nEfforts aux appuis, enveloppe ELU (N vertical en kN, V horizontal en kN, M en kN·m) :")
    appuis = {"Pied de poteau (×4)": [f"S{n}" for n in coins],
              "Pied de limon V1 (×2)": ["LV10s", "LV11s"],
              "Arrivée limon V2 (×2)": ["LV20s", "LV21s"]}
    for nom, noeuds in appuis.items():
        n = m.nodes
        N = max(abs(n[k].RxnFY[c]) for k in noeuds for c in elu) / 1e3
        V = max(sqrt(n[k].RxnFX[c] ** 2 + n[k].RxnFZ[c] ** 2) for k in noeuds for c in elu) / 1e3
        M = max(sqrt(n[k].RxnMX[c] ** 2 + n[k].RxnMZ[c] ** 2) for k in noeuds for c in elu) / 1e6
        print(f"  {nom:24} N = {N:5.2f}   V = {V:5.2f}   M = {M:5.2f}")


def _auto_controle():
    # Axe fort bien affecté : poutre UPE sur 2 appuis, flèche = 5 w L⁴ / 384 E I
    m = nouveau_modele()
    m.add_node("a", 0, 0, 0)
    m.add_node("b", 4000, 0, 0)
    m.def_support("a", True, True, True, True, False, False)
    m.def_support("b", False, True, True, False, False, False)
    m.add_member("p", "a", "b", "acier", "UPE")
    m.add_member_dist_load("p", "FY", -1, -1, case="G")
    m.add_load_combo("C", {"G": 1})
    m.analyze()
    assert isclose(-m.members["p"].min_deflection("dy", "C"), 5 * 4000**4 / (384 * E_acier * upe_I), rel_tol=1e-3)
    assert isclose(-m.members["p"].min_moment("Mz", "C"), 4000**2 / 8, rel_tol=1e-3)  # moment positif = négatif dans PyNite
    assert 2.3e6 < upe_Iz < 2.6e6 and 25 < e_cc < 40  # ordres de grandeur d'un UPE 220


if __name__ == "__main__":
    _auto_controle()
    modele = construire()
    print(f"Escalier {nb_volee1}/{nb_volee2} — modèle en barres PyNite")
    print(f"UPE 220 calculé : Iz = {upe_Iz / 1e4:.0f} cm⁴, J = {upe_J / 1e4:.1f} cm⁴, "
          f"centre de cisaillement à {e_cc:.0f} mm de l'âme")
    resultats(*modele)
    print()
    afficher()
    print("\nNon calculé : déversement, gauchissement (torsion non uniforme), assemblages, chevilles,"
          " vibrations, chargement alterné d'une seule volée.")

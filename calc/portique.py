"""Modèle en barres de l'escalier gab (PyNite) : stabilité, torsion de la poutre avant, efforts aux appuis.

Reprend les paramètres et hypothèses de calc/predim.py. Ordres de grandeur, pas une note de calcul.
Installer : pip install PyNiteFEA. Lancer : python3 calc/portique.py

Appuis : pieds encastrés au sol (platine à 4 chevilles) ; bas des limons V1 articulé (2 chevilles alignées
dans l'axe du limon, D28) ; haut des limons V2 articulé (boulonné à la structure supérieure) ; limons
articulés sur la poutre avant (platines boulonnées). Tête des pieds (platine boulonnée par 2 M12 sous le cadre) :
calculée rigide puis articulée, les deux bornes. Les marches ne relient pas les limons entre eux (côté sécurité).
Contreventement en travers (D30) : une diagonale en tube par face d'about du palier (avant et arrière, en sens
opposés), articulée en tête d'un pied et au pied de l'autre.
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
diag_cote, diag_ep = 50, 3  # diagonales de contreventement, tube carré supposé
c, t = diag_cote, diag_ep
diag_A, diag_I = c**2 - (c - 2 * t) ** 2, (c**4 - (c - 2 * t) ** 4) / 12
g_acier = 7.85e-5  # N/mm³
cheville_a = 180 / 2 - 40 / 2  # chevilles des pieds : platine de 180, au milieu de la marge de 40 (± 70 mm)

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
    m.add_section("diag", diag_A, diag_I, diag_I, (diag_cote - diag_ep) ** 3 * diag_ep)
    # Liaisons d'excentricité de 29 mm (platines / poutre avant), pas la tête des pieds (releases de construire()) ;
    # 400 × l'UPE : au-delà, le solveur rejetait le système mal conditionné du palier sans diagonales
    m.add_section("rigide", 1e6, 1e10, 1e10, 1e10)
    return m


def noeud(m, nom, x, y, z):
    return m.add_node(nom, x, z, y)  # PyNite veut Y vertical : (x, y, z) → (x, z, y)


def construire(tete_rigide=True, diagonales=True):
    m = nouveau_modele()
    tot = {}  # charges appliquées par (cas, direction PyNite), pour le contrôle d'équilibre

    def charge(barre, cas, w, d="FY"):
        """Charge répartie w, positive vers le bas pour FY, dans le sens de l'axe sinon."""
        w = -w if d == "FY" else w
        m.add_member_dist_load(barre, d, w, w, case=cas)
        tot[cas, d] = tot.get((cas, d), 0.0) + w * m.members[barre].L()

    def force(noeud_, cas, F, d):
        m.add_node_load(noeud_, d, F, case=cas)
        tot[cas, d] = tot.get((cas, d), 0.0) + F

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
        if not tete_rigide:
            m.def_releases(f"T{haut}", Ryj=True, Rzj=True)
        charge(f"T{haut}", "G", tube_A * g_acier)

    # Diagonales : face avant du sol en -Y à la tête en +Y, face arrière en sens inverse
    if diagonales:
        for nom, bas, haut in (("DA", "SA0", f"A{len(ys) - 1}"), ("DB", "SB1", "B0")):
            m.add_member(nom, bas, haut, "acier", "diag")
            m.def_releases(nom, Ryi=True, Rzi=True, Ryj=True, Rzj=True)
            charge(nom, "G", diag_A * g_acier)

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
                m.def_support(f"{nom}s", True, True, True, False, False, False)
                m.add_member(nom, f"{nom}s", f"{nom}p", "acier", "UPE")
                m.def_releases(nom, Ryj=True, Rzj=True)
            else:
                noeud(m, f"{nom}s", X_a, y, hauteur_totale - dz)
                m.def_support(f"{nom}s", True, True, True, True, False, False)  # RX bloqué : pas de rotation sur l'axe
                m.add_member(nom, f"{nom}p", f"{nom}s", "acier", "UPE")
                m.def_releases(nom, Ryi=True, Rzi=True)
            charge(nom, "G", wl_G)
            charge(nom, "Q", wl_Q)
            charge(nom, "GCY", q_gc, "FZ")

    # Poussée sur les mains courantes, toutes dans le sens des défauts de verticalité (côté sécurité), appliquée
    # à l'axe des barres : en travers (Y) sur les 4 limons et les poutres latérales, en long (X) sur la poutre arrière.
    # shortcut: pas de moment dû à la hauteur de la main courante ; ordre de grandeur dans torsion_limons()
    for b in ("PL1", "PL2"):
        charge(b, "GCY", q_gc, "FZ")
    charge("PB", "GCX", q_gc, "FX")
    # Poids des mains courantes et potelets (g_gc de predim.py), sur les mêmes lignes
    for b in (*(f"L{v}{k}" for v in y_limons for k in (0, 1)), "PL1", "PL2", "PB"):
        charge(b, "G", g_gc)

    # Défauts de verticalité (EN 1993-1-1 §5.3.2) en forces horizontales aux 4 angles du palier
    alpha_h = min(1.0, max(2 / 3, 2 / sqrt(Z_c / 1000)))
    phi = 1 / 200 * alpha_h * sqrt(0.5 * (1 + 1 / 4))
    G, Q = -tot["G", "FY"], -tot["Q", "FY"]
    H = phi * (1.35 * G + 1.5 * Q) / 4
    for coin in coins:
        force(coin, "HX", H, "FX")
        force(coin, "HY", H, "FZ")
    r = (G + Q) / (1.35 * G + 1.5 * Q)  # même défaut, sous charges ELS
    # Poussée et défauts dans les deux sens ; « _sou » : G favorable, pour le soulèvement des chevilles
    for d in ("X", "Y"):
        for s, sens in ((1, ""), (-1, "-")):
            m.add_load_combo(f"ELU_{d}{sens}", {"G": 1.35, "Q": 1.5, f"H{d}": s})
            m.add_load_combo(f"ELS_{d}{sens}", {"G": 1.0, "Q": 1.0, f"H{d}": s * r})
            m.add_load_combo(f"ELU_GC{d}{sens}", {"G": 1.35, f"GC{d}": 1.5 * s, "Q": 1.05, f"H{d}": s})
            m.add_load_combo(f"ELU_GC{d}{sens}_sou", {"G": 1.0, f"GC{d}": 1.5 * s, f"H{d}": s})
            m.add_load_combo(f"ELS_GC{d}{sens}", {"G": 1.0, f"GC{d}": s, "Q": 0.7, f"H{d}": s * r})
    # shortcut: Q partout en même temps, pas de chargement alterné d'une seule volée ; à ajouter si une vérif est limite
    m.analyze(check_statics=False)  # la table de PyNite est remplacée par l'assertion d'équilibre qui suit
    equilibre(m, tot)
    return m, poutres_avant, coins


def equilibre(m, tot):
    """Somme des réactions + charges appliquées = 0, dans les 3 directions, pour chaque combinaison."""
    for nom, combo in m.load_combos.items():
        for d in ("FX", "FY", "FZ"):
            F = sum(f * tot.get((cas, d), 0.0) for cas, f in combo.factors.items())
            R = sum(getattr(n, f"Rxn{d}").get(nom, 0.0) for n in m.nodes.values())
            assert isclose(F + R, 0, abs_tol=1e-6 * max(abs(F), 1e3)), (nom, d, F, R)


def resultats(m, poutres_avant, coins, tete_rigide=True):
    elu = [c for c in m.load_combos if c.startswith("ELU")]
    els = [c for c in m.load_combos if c.startswith("ELS")]
    diagonales = "DA" in m.members
    # Stabilité : déplacement horizontal du palier, en long (X) et en travers (Y)
    for d, ddl in (("X", "DX"), ("Y", "DZ")):
        u = max(abs(getattr(m.nodes[n], ddl)[c]) for n in coins for c in els)
        verif(f"Palier, en {'long' if d == 'X' else 'travers'} ({d})", "dépl. horiz. ELS", u, Z_c / 300, "mm")

    # Poutre avant : flexion forte + faible, puis torsion de Saint-Venant
    sigma = max(abs(m.members[b].max_moment("Mz", c)) / upe_W + abs(m.members[b].max_moment("My", c)) / upe_Wz
                for b in poutres_avant for c in elu)
    sigma = max(sigma, max(abs(m.members[b].min_moment("Mz", c)) / upe_W + abs(m.members[b].min_moment("My", c)) / upe_Wz
                           for b in poutres_avant for c in elu))
    T = max(max(abs(m.members[b].max_torque(c)), abs(m.members[b].min_torque(c))) for b in poutres_avant for c in elu)
    verif("Poutre avant UPE 220", "flexion ELU", sigma, fy / gM0, "MPa")
    verif("Poutre avant UPE 220", "torsion ELU", T * limon_tf / upe_J, fy / sqrt(3) / gM0, "MPa")

    # Pieds : flambement + flexion ; L_cr = H si le palier est contreventé ou la tête rigide, 2 H sinon.
    # H à l'axe du cadre (longueur de la barre), 110 mm de plus que le pied réel de predim.py : côté sécurité
    H = Z_c
    N_b = flambement(1, (1 if tete_rigide or diagonales else 2) * H, tube_A, tube_I)
    taux = 0.0
    for p in (f"T{n}" for n in coins):
        for c in elu:
            N = m.members[p].max_axial(c)  # PyNite : compression positive
            M = max(abs(m.members[p].max_moment(a, c)) for a in ("My", "Mz"))
            M = max(M, max(abs(m.members[p].min_moment(a, c)) for a in ("My", "Mz")))
            taux = max(taux, N / N_b + M / (tube_W * fy / gM0))
    verif(f"Pieds tube {poteau_cote}×{poteau_ep}", "N + M ELU", taux, 1.0, "taux")

    if diagonales:
        L = m.members["DA"].L()
        Nc = max(m.members[d].max_axial(c) for d in ("DA", "DB") for c in elu)
        Nt = -min(m.members[d].min_axial(c) for d in ("DA", "DB") for c in elu)
        verif(f"Diagonales tube {diag_cote}×{diag_ep} (L = {L:.0f})", "flambement ELU", Nc / 1e3,
              flambement(1, L, diag_A, diag_I) / 1e3, "kN")
        verif(f"Diagonales tube {diag_cote}×{diag_ep}", "traction ELU", Nt / 1e3, diag_A * fy / gM0 / 1e3, "kN")

    # Limons : flexion forte (charges verticales) + faible (poussée des mains courantes)
    def m_max(barre, axe, c):
        return max(abs(m.members[barre].max_moment(axe, c)), abs(m.members[barre].min_moment(axe, c)))

    for v in ("V1", "V2"):
        sigma = max(m_max(f"L{v}{k}", "Mz", c) / upe_W + m_max(f"L{v}{k}", "My", c) / upe_Wz
                    for k in (0, 1) for c in elu)
        verif(f"Limons {v} UPE 220", "flexion ELU", sigma, fy / gM0, "MPa")

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
    soul = -min(m.nodes[f"S{n}"].RxnFY[c] for n in coins for c in elu) / 1e3
    print(f"  Soulèvement maxi d'un pied de poteau : {max(soul, 0):5.2f} kN (G favorable : « _sou »)")

    # Chevilles, platine rigide tournant autour de son centre (côté sécurité, le béton comprimé n'est pas compté) :
    # pieds de poteau 4 chevilles à ± cheville_a ; pieds de limons V1 articulés, 2 chevilles
    n = m.nodes
    T_p = max(-n[k].RxnFY[c] / 4 + (abs(n[k].RxnMX[c]) + abs(n[k].RxnMZ[c])) / (4 * cheville_a)
              for k in appuis["Pied de poteau (×4)"] for c in elu)
    V_p = max(sqrt(n[k].RxnFX[c] ** 2 + n[k].RxnFZ[c] ** 2) / 4 for k in appuis["Pied de poteau (×4)"] for c in elu)
    T_l = max(-n[k].RxnFY[c] / 2 for k in appuis["Pied de limon V1 (×2)"] for c in elu)
    V_l = max(sqrt(n[k].RxnFX[c] ** 2 + n[k].RxnFZ[c] ** 2) / 2 for k in appuis["Pied de limon V1 (×2)"] for c in elu)
    print(f"  Chevilles M12, par cheville (enveloppes séparées) : pieds de poteau T = {max(T_p, 0) / 1e3:5.2f}"
          f"  V = {V_p / 1e3:5.2f} kN ; pieds de limons V1 T = {max(T_l, 0) / 1e3:5.2f}  V = {V_l / 1e3:5.2f} kN")
    print("  Résistance des chevilles : à prendre dans l'ETA de la cheville choisie, selon le béton de la dalle"
          " (non fournis)")


def torsion_limons():
    """Ordre de grandeur hors modèle : poussée à hauteur de main courante → torsion de Saint-Venant des limons seuls.

    Couple réparti 1,5 q_gc × (main courante → centre de cisaillement, à mi-hauteur du limon). Appuis du modèle :
    V1 libre en torsion au pied (chevilles dans l'axe), V2 tenu aux deux bouts. Les marches qui relient les deux
    limons d'une volée et le gauchissement de l'UPE ne sont pas comptés : borne haute.
    """
    t = 1.5 * q_gc * (mc_h + limon_descente + limon_h / 2)
    for v, L_h, k in (("V1", X_r - X_0, 1), ("V2", X_r - X_a, 0.5)):
        T = k * t * L_h / cos(angle)
        verif(f"Limons {v} seuls (T = {T / 1e6:.1f} kN·m)", "torsion ELU", T * limon_tf / upe_J, fy / sqrt(3) / gM0, "MPa")


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
    # Signe de l'effort normal : un poteau comprimé a un effort normal positif
    m.add_node("h", 0, 1000, 0)
    m.add_member("c", "a", "h", "acier", "tube")
    m.add_node_load("h", "FY", -1000, case="G")
    m.analyze()
    assert isclose(m.members["c"].max_axial("C"), 1000, rel_tol=1e-3)
    assert 2.3e6 < upe_Iz < 2.6e6 and 25 < e_cc < 40  # ordres de grandeur d'un UPE 220


if __name__ == "__main__":
    _auto_controle()
    print(f"Escalier {nb_volee1}/{nb_volee2} — modèle en barres PyNite")
    print(f"UPE 220 calculé : Iz = {upe_Iz / 1e4:.0f} cm⁴, J = {upe_J / 1e4:.1f} cm⁴, "
          f"centre de cisaillement à {e_cc:.0f} mm de l'âme")
    print("\n=== Hors modèle ===")
    torsion_limons()
    afficher()
    for tete_rigide in (True, False):
        print(f"\n=== Tête des pieds {'rigide' if tete_rigide else 'articulée'} ===")
        lignes.clear()
        resultats(*construire(tete_rigide), tete_rigide)
        print()
        afficher()
    print("\nNon calculé : déversement, gauchissement (torsion non uniforme), marches comme traverses entre limons,"
          " assemblages (soudures, platines, résistance des chevilles), vibrations, chargement alterné d'une seule volée.")

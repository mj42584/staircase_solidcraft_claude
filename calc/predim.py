"""Prédimensionnement de l'escalier gab : ordres de grandeur, pas une note de calcul.

Les paramètres sont recopiés de cad/escalier.solidcraft (CONCEPTION.md §3) : les tenir à jour
à la main quand le modèle change. Unités : N, mm, MPa. Lancer : python3 calc/predim.py
"""
from math import atan, cos, degrees, isclose, sqrt

# --- Paramètres du modèle (CONCEPTION.md §3)
hauteur_totale = 3848
nb_contremarches = 22
nb_volee1 = 15
giron = 274
emmarchement = 1000
jeu_limons = 100
palier_profondeur = 1000
marche_epaisseur = 60
palier_ep = marche_epaisseur
limon_h, limon_b, limon_tw, limon_tf = 220, 85, 6.5, 12
poteau_cote, poteau_ep = 100, 5
boulon_d = 12
platine_ep = 15
mc_h, mc_cote, mc_palier_h = 900, 45, 1000
limon_descente = 30   # limons descendus de 30 mm en vertical (limon_dessus, D17)
potelet_l, potelet_ep = 40, 3   # 30 × 2 dans le modèle, 40 × 3 à l'essai (D34 ; épaisseur supposée)
nb_potelets_v1, nb_potelets_v2, nb_potelets_fond = 5, 3, 4   # V1 : 5 (D32) ; fond : 3 dans le modèle, 4 à l'essai (D34)
platine_bas_b, platine_bas_ep, boulon_potelet_d = 50, 10, 8   # platine basse 10 mm depuis D39 (8 avant)
platine_haut_entraxe, potelet_fond_marge = 80, 25

hauteur_marche = hauteur_totale / nb_contremarches
nb_volee2 = nb_contremarches - nb_volee1
angle = atan(hauteur_marche / giron)
jour = 2 * limon_b + jeu_limons
L_p = 2 * (emmarchement + limon_b) + jour   # largeur du palier hors tout = poutre avant
# Pas des potelets, comme dans le modèle : V1 de giron / 2 à rive_x - giron / 2 - platine_ep (en plan) ;
# fond du palier : 2 * potelet_fond_y / (nb - 1)
pas_potelets_v1 = ((nb_volee1 - 1) * giron - giron - platine_ep) / (nb_potelets_v1 - 1) / cos(angle)
# V2 : ext du premier potelet (X = rive_x - 3 giron / 2) au dernier (X = X_a + giron / 2 + platine_ep) ; int du premier
# (rive_x - platine_ep - giron / 2, D25) au même dernier
pas_potelets_v2_ext = ((nb_volee2 - 2) * giron - platine_ep) / (nb_potelets_v2 - 1) / cos(angle)
pas_potelets_v2_int = ((nb_volee2 - 1) * giron - 2 * platine_ep) / (nb_potelets_v2 - 1) / cos(angle)
pas_potelets_fond = 2 * (L_p / 2 - limon_b / 2 - mc_cote / 2 - platine_haut_entraxe / 2 - potelet_fond_marge) / (nb_potelets_fond - 1)

# --- Hypothèses, à faire valider par un bureau d'études
q_k = 2.5e-3          # N/mm² : escalier de logement (cat. A), AN française de l'EN 1991-1-1
Q_k = 2000            # N : charge ponctuelle, vérifications locales, non cumulée avec q_k
q_gc = 0.6            # N/mm : poussée horizontale sur les mains courantes, cat. A (AN française), validée par l'utilisateur le 2026-11-03
g_chene = 7.5e-6      # N/mm³ (0,75 g/cm³, comme le modèle)
equerres_g = 2 * 200 * 0.037   # N par marche : 2 cornières 50×50×5 de 200 mm (3,77 kg/m, essai D32 ; 30×30×3 : 0,0133)
# Chêne D30 (EN 338), classe de service 1, charge de moyen terme
fmk_bois, E_bois, kmod, gM_bois = 30, 11000, 0.8, 1.3
# Vis à bois de la cornière dans la marche (D35) : 3 vis par cornière, Ø5, 50 mm dans le chêne, en ligne le long du giron
# (positions supposées). Raideur axiale 25 d l_ef par vis (Blass-Sandhaas, de mémoire), plafond : sans l'aile de 5 mm ni le limon.
vis_d, vis_lef, vis_x = 5, 50, (-75, 0, 75)
K_VIS = 25 * vis_d * vis_lef * sum(x**2 for x in vis_x)   # N·mm/rad, 7,0e7
rho_k = 530   # kg/m³, masse volumique caractéristique du D30 (EN 338, de mémoire ; 640 = moyenne) ; 700 avant D40
# EC5 éq. (8.39) : f_ax,k = 0,52 d^-0,5 l_ef^-0,1 ρk^0,8 (exposants négatifs : la résistance unitaire baisse avec d et l_ef),
# puis F = n_ef f_ax,k d l_ef ; formule donnée pour 6 ≤ d ≤ 12 mm, appliquée ici à Ø5 (ordre de grandeur)
F_arrachement = 0.8 * 0.52 * vis_d**-0.5 * vis_lef**-0.1 * rho_k**0.8 * vis_d * vis_lef / 1.3   # N, kmod 0,8, gM 1,3

# Chevilles M12 des pieds (D37) : béton C25/30 non fissuré (choix de l'utilisateur), dalle et distances au bord NON fournies ; cheville
# non choisie : acier 8.8, hef = 70 mm supposés, formules EN 1992-4 de mémoire, à remplacer par l'ETA de la cheville retenue.
fck_beton, hef, As_ch, fuk_ch = 25, 70, 84.3, 800
gM_ch_acier_N, gM_ch_acier_V, gM_ch_beton = 1.5, 1.25, 1.8
N0_c = 11.0 * sqrt(fck_beton) * hef**1.5            # N, cône de béton d'une cheville, non fissuré
k_groupe = ((140 + 3 * hef) / (3 * hef)) ** 2 / 4   # groupe de 4 à 140 mm, loin des bords, par cheville (2 à 80 mm : 0,69 aussi)
N_Rd_c = k_groupe * N0_c / gM_ch_beton              # arrachement-cône
N_Rd_s = As_ch * fuk_ch / gM_ch_acier_N             # rupture de l'acier en traction
V_Rd_s = 0.5 * As_ch * fuk_ch / gM_ch_acier_V       # rupture de l'acier en cisaillement (sans mortier)
V_Rd_cp = 2 * N_Rd_c                                # effet de levier (k8 = 2)


def V_Rd_bord(c1, d=12):
    """Cisaillement vers un bord à c1 mm, une cheville seule, béton non fissuré (EN 1992-4 §7.2.2.5)."""
    alpha, beta = 0.1 * sqrt(hef / c1), 0.1 * (d / c1) ** 0.2
    return 1.7 * d**alpha * hef**beta * sqrt(fck_beton) * c1**1.5 / gM_ch_beton
# Acier S235 : nuance supposée, elle n'est pas fixée dans CONCEPTION.md
fy, E_acier, gM0, gM1 = 235, 210000, 1.0, 1.0
# UPE 220, catalogue EN 10365, flexion autour de l'axe fort
upe_I, upe_W, upe_g = 26.8e6, 244e3, 0.266   # mm⁴, mm³, N/mm (26,6 kg/m)
# Boulons classe 8.8 supposée
fub, As_M12, As_M8, gM2 = 800, 84.3, 36.6, 1.25
# Mains courantes et potelets : 26,6 kg de chêne + 16 × 3,489 + 8 × 3,742 kg de potelets 40 × 40 × 3 (volumes de
# `measure` × 7,85 g/cm³, D34 ; avant : 12 × 2,006 + 7 × 2,134 en 30 × 2), répartis sur les lignes de main courante : 4 limons, 2 côtés et le fond du palier
L_lignes = 2 * ((nb_volee1 - 1) + nb_volee2) * giron / cos(angle) + 2 * palier_profondeur + L_p
g_gc = 9.81 * (26.6 + 16 * 3.489 + 8 * 3.742) / L_lignes   # N/mm de ligne
fleche_max = 300      # L/300


def poutre(L, w=0.0, charges=(), EI=1.0, n=1000):
    """Poutre sur 2 appuis : (moment max, flèche max) sous une charge répartie w et des charges (P, a)."""
    M = f = 0.0
    for i in range(n + 1):
        x = L * i / n
        m = w * x * (L - x) / 2
        d = w * x * (L**3 - 2 * L * x**2 + x**3) / 24
        for P, a in charges:
            b = L - a
            if x <= a:
                m += P * b * x / L
                d += P * b * x * (L**2 - b**2 - x**2) / (6 * L)
            else:
                m += P * a * (L - x) / L
                d += P * a * (L - x) * (2 * L * x - x**2 - a**2) / (6 * L)
        M, f = max(M, m), max(f, d)
    return M, f / EI


def reaction_gauche(L, w=0.0, charges=()):
    return w * L / 2 + sum(P * (L - a) / L for P, a in charges)


lignes = []


def verif(element, critere, valeur, limite, unite):
    lignes.append((element, critere, valeur, limite, unite))


def marche(ep):
    """(contrainte ELU, flèche ELS) d'une marche d'épaisseur ep, portée emmarchement, sur 2 appuis."""
    L, b = emmarchement, giron
    EI, W = E_bois * b * ep**3 / 12, b * ep**2 / 6
    g = g_chene * b * ep
    M_q, _ = poutre(L, w=1.35 * g + 1.5 * q_k * b, EI=EI)
    M_Q, _ = poutre(L, w=1.35 * g, charges=[(1.5 * Q_k, L / 2)], EI=EI)
    _, f_q = poutre(L, w=g + q_k * b, EI=EI)
    _, f_Q = poutre(L, w=g, charges=[(Q_k, L / 2)], EI=EI)
    return max(M_q, M_Q) / W, max(f_q, f_Q)


def flambement(N, L_cr, A, I):
    """Taux N / Nb,Rd, courbe c (tube formé à froid), EN 1993-1-1 §6.3.1."""
    lam = L_cr / sqrt(I / A) / (93.9 * sqrt(235 / fy))
    phi = 0.5 * (1 + 0.49 * (lam - 0.2) + lam**2)
    chi = min(1.0, 1 / (phi + sqrt(phi**2 - lam**2)))
    return chi * A * fy / gM1


def limons_et_poutre_avant():
    """Charges des limons (N/mm), réactions sur la poutre avant (ELU, ELS) et moment ELU de la poutre avant."""
    marche_g = g_chene * giron * marche_epaisseur * emmarchement + equerres_g
    w_G = marche_g / 2 / giron + (upe_g + g_gc) / cos(angle)
    w_Q = q_k * emmarchement / 2
    w_elu, w_els = 1.35 * w_G + 1.5 * w_Q, w_G + w_Q
    L_h = {"V1": (nb_volee1 - 1) * giron, "V2": nb_volee2 * giron}
    R = {v: (w_elu * L / 2, w_els * L / 2) for v, L in L_h.items()}
    # Poutre avant du palier : reçoit les 4 limons (charges au milieu des ailes), appuis aux angles extérieurs
    x_limons = (limon_b / 2, L_p / 2 - jour / 2 + limon_b / 2, L_p / 2 + jour / 2 - limon_b / 2, L_p - limon_b / 2)
    w_palier_G = g_chene * palier_ep * palier_profondeur / 2 + upe_g
    w_palier_Q = q_k * palier_profondeur / 2
    charges = lambda i: list(zip((R["V1"][i], R["V1"][i], R["V2"][i], R["V2"][i]), x_limons))
    w_p_elu, w_p_els = 1.35 * w_palier_G + 1.5 * w_palier_Q, w_palier_G + w_palier_Q
    M_pa, _ = poutre(L_p, w=w_p_elu, charges=charges(0), EI=E_acier * upe_I)
    return dict(marche_g=marche_g, w_G=w_G, w_Q=w_Q, w_elu=w_elu, w_els=w_els, L_h=L_h, R=R, x_limons=x_limons,
                w_palier_G=w_palier_G, w_palier_Q=w_palier_Q, w_p_elu=w_p_elu, w_p_els=w_p_els, charges=charges, M_pa=M_pa)


def calculer():
    # Marches (chêne) : portée = emmarchement, appuis simples sur les équerres (côté sécurité)
    sigma, f = marche(marche_epaisseur)
    f_bois = kmod * fmk_bois / gM_bois
    verif(f"Marche chêne {marche_epaisseur} mm", "contrainte ELU", sigma, f_bois, "MPa")
    verif(f"Marche chêne {marche_epaisseur} mm", "flèche ELS", f, emmarchement / fleche_max, "mm")
    ep_mini = marche_epaisseur
    while marche(ep_mini)[0] > f_bois or marche(ep_mini)[1] > emmarchement / fleche_max:
        ep_mini += 1

    # Limons : poutre inclinée sur 2 appuis, charges données par mètre horizontal, une demi-volée par limon
    e = limons_et_poutre_avant()
    R, charges, w_p_elu, w_p_els = e["R"], e["charges"], e["w_p_elu"], e["w_p_els"]
    for nom, L_h in e["L_h"].items():
        L_s = L_h / cos(angle)
        M = e["w_elu"] * L_h**2 / 8
        f = 5 * e["w_els"] * cos(angle) ** 2 * L_s**4 / (384 * E_acier * upe_I)
        verif(f"Limon {nom} UPE 220 (L = {L_s:.0f})", "contrainte ELU", M / upe_W, fy / gM0, "MPa")
        verif(f"Limon {nom} UPE 220 (L = {L_s:.0f})", "flèche ELS", f, L_s / fleche_max, "mm")

    _, f = poutre(L_p, w=w_p_els, charges=charges(1), EI=E_acier * upe_I)
    verif(f"Poutre avant UPE 220 (L = {L_p:.0f})", "contrainte ELU", e["M_pa"] / upe_W, fy / gM0, "MPa")
    verif(f"Poutre avant UPE 220 (L = {L_p:.0f})", "flèche ELS", f, L_p / fleche_max, "mm")

    # Pieds avant : pied côté V1 (le plus chargé), libre en tête faute de contreventement → L_cr = 2 H
    N = reaction_gauche(L_p, w=w_p_elu, charges=charges(0))
    H = nb_volee1 * hauteur_marche - palier_ep - limon_h
    A = poteau_cote**2 - (poteau_cote - 2 * poteau_ep) ** 2
    I = (poteau_cote**4 - (poteau_cote - 2 * poteau_ep) ** 4) / 12
    verif(f"Pied tube {poteau_cote}×{poteau_ep} (H = {H:.0f})", "flambement ELU", N / 1e3, flambement(N, 2 * H, A, I) / 1e3, "kN")

    # Boulons des platines côté palier : 2 boulons en cisaillement par platine
    verif(f"Boulons M{boulon_d} 8.8 platine V1", "cisaillement ELU", R["V1"][0] / 2 / 1e3, 0.6 * fub * As_M12 / gM2 / 1e3, "kN")

    # Potelets en console sous la poussée des mains courantes : un pas de main courante par potelet,
    # bras de levier du dessus du limon (ou du plancher) à l'axe de la main courante
    c, t = potelet_l, potelet_ep
    W = (c**4 - (c - 2 * t) ** 4) / 12 / (c / 2)   # angles vifs
    for nom, pas, h in (("V1", pas_potelets_v1, mc_h + limon_descente), ("V2 ext", pas_potelets_v2_ext, mc_h + limon_descente),
                        ("V2 int", pas_potelets_v2_int, mc_h + limon_descente), ("fond", pas_potelets_fond, mc_palier_h)):
        M = 1.5 * q_gc * pas * h
        verif(f"Potelet {nom} {c}×{t} (pas {pas:.0f}, h {h:.0f})", "flexion ELU", M / W, fy / gM0, "MPa")
        if nom.startswith("V"):
            # 2 vis M8 dans l'axe du limon, platine basculant sur son bord : bras de levier b / 2, sans effet de levier
            T = M / (platine_bas_b / 2) / 2
            verif(f"Boulons M{boulon_potelet_d} 8.8 platine potelet {nom}", "traction ELU", T / 1e3,
                  0.9 * fub * As_M8 / gM2 / 1e3, "kN")
    return ep_mini


def afficher():
    print(f"{'Élément':38} {'Critère':16} {'Valeur':>9} {'Limite':>9}  Taux  ")
    for element, critere, valeur, limite, unite in lignes:
        taux = valeur / limite
        print(f"{element:38} {critere:16} {valeur:9.2f} {limite:9.2f}  {taux:4.0%}  "
              f"{'OK' if taux <= 1 else 'NON'}  {unite}")


def _auto_controle():
    M, f = poutre(1000, charges=[(1, 500)])
    assert isclose(M, 250) and isclose(f, 1000**3 / 48)
    M, f = poutre(1000, w=1)
    assert isclose(M, 1000**2 / 8) and isclose(f, 5 * 1000**4 / 384)
    assert isclose(reaction_gauche(1000, charges=[(1, 250)]), 0.75)
    assert round(2 * hauteur_marche + giron) == 624   # Blondel de CONCEPTION.md
    assert isclose(pas_potelets_v1 * cos(angle), (2501.67 - 1319.33) * 3 / (nb_potelets_v1 - 1), abs_tol=0.1)   # relevé à 4 potelets dans le modèle, 5 prévus
    assert isclose(pas_potelets_v2_ext * cos(angle), 677.5, abs_tol=0.1) and isclose(pas_potelets_v2_int * cos(angle), 807.0, abs_tol=0.1)  # relevé D32
    assert isclose(pas_potelets_fond, 2 * 1090 / (nb_potelets_fond - 1), abs_tol=0.1)                          # potelet_fond_y = 1 090


if __name__ == "__main__":
    _auto_controle()
    ep_mini = calculer()
    print(f"Escalier {nb_volee1}/{nb_volee2}, h = {hauteur_marche:.2f} mm, angle {degrees(angle):.2f}°, "
          f"Blondel {2 * hauteur_marche + giron:.0f}")
    afficher()
    print(f"\nÉpaisseur mini des marches chêne pour passer : {ep_mini} mm")
    print("Stabilité, torsion : portique.py ; assemblages, déversement, gauchissement, vibrations : assemblages.py."
          " Non calculé : fluage du chêne.")

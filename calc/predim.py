"""Prédimensionnement de l'escalier gab : ordres de grandeur, pas une note de calcul.

Les paramètres sont recopiés de cad/escalier.solidcraft (CONCEPTION.md §3) : les tenir à jour
à la main quand le modèle change. Unités : N, mm, MPa. Lancer : python3 calc/predim.py
"""
from math import atan, cos, degrees, isclose, sqrt

# --- Paramètres du modèle (CONCEPTION.md §3)
hauteur_totale = 3800
nb_contremarches = 22
nb_volee1 = 17
giron = 274
emmarchement = 1000
jeu_limons = 100
palier_profondeur = 1000
marche_epaisseur = 30
palier_ep = marche_epaisseur
limon_h, limon_b, limon_tw, limon_tf = 220, 85, 6.5, 12
poteau_cote, poteau_ep = 100, 5
boulon_d = 12

hauteur_marche = hauteur_totale / nb_contremarches
nb_volee2 = nb_contremarches - nb_volee1
angle = atan(hauteur_marche / giron)
jour = 2 * limon_b + jeu_limons

# --- Hypothèses, à faire valider par un bureau d'études
q_k = 2.5e-3          # N/mm² : escalier de logement (cat. A), AN française de l'EN 1991-1-1
Q_k = 2000            # N : charge ponctuelle, vérifications locales, non cumulée avec q_k
g_chene = 7.5e-6      # N/mm³ (0,75 g/cm³, comme le modèle)
equerres_g = 2 * 200 * 0.0133   # N par marche : 2 cornières 30×30×3 de 200 mm (1,36 kg/m)
# Chêne D30 (EN 338), classe de service 1, charge de moyen terme
fmk_bois, E_bois, kmod, gM_bois = 30, 11000, 0.8, 1.3
# Acier S235 : nuance supposée, elle n'est pas fixée dans CONCEPTION.md
fy, E_acier, gM0, gM1 = 235, 210000, 1.0, 1.0
# UPE 220, catalogue EN 10365, flexion autour de l'axe fort
upe_I, upe_W, upe_g = 26.8e6, 244e3, 0.266   # mm⁴, mm³, N/mm (26,6 kg/m)
# Boulons classe 8.8 supposée
fub, As_M12, gM2 = 800, 84.3, 1.25
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
    marche_g = g_chene * giron * marche_epaisseur * emmarchement + equerres_g
    w_G = marche_g / 2 / giron + upe_g / cos(angle)
    w_Q = q_k * emmarchement / 2
    w_elu, w_els = 1.35 * w_G + 1.5 * w_Q, w_G + w_Q
    R = {}
    for nom, L_h in (("V1", (nb_volee1 - 1) * giron), ("V2", nb_volee2 * giron)):
        L_s = L_h / cos(angle)
        M = w_elu * L_h**2 / 8
        f = 5 * w_els * cos(angle) ** 2 * L_s**4 / (384 * E_acier * upe_I)
        verif(f"Limon {nom} UPE 220 (L = {L_s:.0f})", "contrainte ELU", M / upe_W, fy / gM0, "MPa")
        verif(f"Limon {nom} UPE 220 (L = {L_s:.0f})", "flèche ELS", f, L_s / fleche_max, "mm")
        R[nom] = (w_elu * L_h / 2, w_els * L_h / 2)

    # Poutre avant du palier : reçoit les 4 limons (charges au milieu des ailes), appuis aux angles extérieurs
    L_p = 2 * (emmarchement + limon_b) + jour
    x_limons = (limon_b / 2, L_p / 2 - jour / 2 + limon_b / 2, L_p / 2 + jour / 2 - limon_b / 2, L_p - limon_b / 2)
    w_palier_G = g_chene * palier_ep * palier_profondeur / 2 + upe_g
    w_palier_Q = q_k * palier_profondeur / 2
    charges = lambda i: list(zip((R["V1"][i], R["V1"][i], R["V2"][i], R["V2"][i]), x_limons))
    w_p_elu, w_p_els = 1.35 * w_palier_G + 1.5 * w_palier_Q, w_palier_G + w_palier_Q
    M, _ = poutre(L_p, w=w_p_elu, charges=charges(0), EI=E_acier * upe_I)
    _, f = poutre(L_p, w=w_p_els, charges=charges(1), EI=E_acier * upe_I)
    verif(f"Poutre avant UPE 220 (L = {L_p:.0f})", "contrainte ELU", M / upe_W, fy / gM0, "MPa")
    verif(f"Poutre avant UPE 220 (L = {L_p:.0f})", "flèche ELS", f, L_p / fleche_max, "mm")

    # Pieds avant : pied côté V1 (le plus chargé), libre en tête faute de contreventement → L_cr = 2 H
    N = reaction_gauche(L_p, w=w_p_elu, charges=charges(0))
    H = nb_volee1 * hauteur_marche - palier_ep - limon_h
    A = poteau_cote**2 - (poteau_cote - 2 * poteau_ep) ** 2
    I = (poteau_cote**4 - (poteau_cote - 2 * poteau_ep) ** 4) / 12
    verif(f"Pied tube {poteau_cote}×{poteau_ep} (H = {H:.0f})", "flambement ELU", N / 1e3, flambement(N, 2 * H, A, I) / 1e3, "kN")

    # Boulons des platines côté palier : 2 boulons en cisaillement par platine
    verif(f"Boulons M{boulon_d} 8.8 platine V1", "cisaillement ELU", R["V1"][0] / 2 / 1e3, 0.6 * fub * As_M12 / gM2 / 1e3, "kN")
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
    assert round(2 * hauteur_marche + giron) == 619   # Blondel de CONCEPTION.md


if __name__ == "__main__":
    _auto_controle()
    ep_mini = calculer()
    print(f"Escalier {nb_volee1}/{nb_volee2}, h = {hauteur_marche:.2f} mm, angle {degrees(angle):.2f}°, "
          f"Blondel {2 * hauteur_marche + giron:.0f}")
    afficher()
    print(f"\nÉpaisseur mini des marches chêne pour passer : {ep_mini} mm")
    print("Non calculé : stabilité d'ensemble / contreventement, torsion de la poutre avant (UPE chargé"
          " sur l'âme), déversement, soudures, pression diamétrale, vibrations, fluage du chêne.")

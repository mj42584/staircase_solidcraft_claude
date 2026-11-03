"""Vérifications locales hors modèle en barres (D38) : assemblages, déversement, gauchissement, couple de la poussée
sur les poutres du palier, vibrations. Ordres de grandeur, pas une note de calcul.

Efforts : predim.py (réactions des limons, potelets) et portique.py (effort des diagonales). Formules de l'EN 1993-1-8
et de la théorie des poutres à parois minces, de mémoire ; hypothèses marquées « supposé ».
Lancer : ~/.venvs/escalier/bin/python calc/assemblages.py
"""
from math import asin, cos, pi, sin, sqrt

import numpy as np

import portique as p
from predim import *  # noqa: F403

fu = 360                      # MPa, S235
beta_w = 0.8
f_vw = fu / (sqrt(3) * beta_w * gM2)   # résistance de calcul d'un cordon (méthode simplifiée), MPa
G_acier = E_acier / 2.6

# UPE 220 en parois minces : lignes moyennes, centre de cisaillement depuis l'axe de l'âme, gauchissement
h_, b_ = limon_h - limon_tf, limon_b - limon_tw / 2
e0 = 3 * b_**2 * limon_tf / (h_ * limon_tw + 6 * b_ * limon_tf)
upe_Iw = limon_tf * b_**3 * h_**2 / 12 * (3 * b_ * limon_tf + 2 * h_ * limon_tw) / (6 * b_ * limon_tf + h_ * limon_tw)
omega_max = h_ / 2 * (b_ - e0)   # coordonnée sectorielle au bout des ailes, mm²
tau_lim = fy / sqrt(3) / gM0


def efforts_diagonales():
    """Plus grand effort normal d'une diagonale, tête des pieds rigide ou articulée (N), longueur et pente (rad)."""
    N = 0.0
    for tete in (True, False):
        m, _, _ = p.construire(tete)
        elu = [c for c in m.load_combos if c.startswith("ELU")]
        N = max(N, *(abs(f(c)) for d in ("DA", "DB") for c in elu
                     for f in (m.members[d].max_axial, m.members[d].min_axial)))
    b = m.members["DA"]
    return N, b.L(), asin(abs(b.j_node.Y - b.i_node.Y) / b.L())


def tstub(F, t, m, e, l_eff, B_t):
    """Résistance d'un tronçon en T à un boulon (EN 1993-1-8 §6.2.4), modes 1 (méthode 2), 2 et 3 (N)."""
    n, e_w = min(e, 1.25 * m), 16 / 4   # rondelle Ø16 (M8) ou Ø24 (M12) : e_w = d_w / 4, M8 ici
    M_pl = 0.25 * l_eff * t**2 * fy / gM0
    F1 = (8 * n - 2 * e_w) * M_pl / (2 * m * n - e_w * (m + n))
    F2 = (2 * M_pl + n * B_t) / (m + n)
    return min(F1, F2, B_t)


def calculer():
    sigma_lim = fy / gM0

    # --- Diagonales : gousset soudé sur le pied, boulon M12, languette, excentricité
    N, L_d, th = efforts_diagonales()
    F_h, F_v = N * cos(th), N * sin(th)
    a, L_w = 3.5, p.gousset_h   # cordons d'angle de 5 mm (a = 3,5) des deux côtés du gousset, supposé
    sig = F_h / (2 * a * L_w) + F_v * p.gousset_trou_l / (a * L_w**2 / 3)   # traction + flexion du groupe de cordons
    s_perp, t_par = sig / sqrt(2), F_v / (2 * a * L_w)
    verif("Soudure gousset / pied (a 3,5)", "contrainte ELU", sqrt(s_perp**2 + 3 * (s_perp**2 + t_par**2)),
          fu / (beta_w * gM2), "MPa")
    verif("Boulon M12 8.8 diagonale", "cisaillement ELU", N / 1e3, 0.6 * fub * As_M12 / gM2 / 1e3, "kN")
    d0, e1, e2 = 14, 30, p.diag_cote / 2   # languette : trou au bout (languette_trou_bout), demi-largeur
    alpha_b = min(e1 / (3 * d0), fub / fu, 1.0)
    k1 = min(2.8 * e2 / d0 - 1.7, 2.5)
    verif("Languette 10 mm, pression diamétrale", "ELU", N / 1e3, k1 * alpha_b * fu * 12 * 10 / gM2 / 1e3, "kN")
    verif("Languette 10 mm, section nette", "traction ELU", N / 1e3, 0.9 * (p.diag_cote - d0) * 10 * fu / gM2 / 1e3, "kN")
    # Languette soudée dans les fentes du tube : 4 cordons de 80 mm, gorge limitée par la paroi de 3 mm
    verif("Soudure languette / tube (a 2,1)", "cisaillement ELU", N / (4 * 2.1 * 80), f_vw, "MPa")
    # Excentricité : effort au plan de contact gousset / languette, 5 mm de l'axe du tube (10 mm du plan des pieds) ;
    # flexion amplifiée 1 / (1 - N / Ncr) de la diagonale comprimée
    W_d = p.diag_I / (p.diag_cote / 2)
    N_cr = pi**2 * E_acier * p.diag_I / L_d**2
    taux = N / flambement(1, L_d, p.diag_A, p.diag_I) + N * 5 / (1 - N / N_cr) / (W_d * fy / gM1)
    verif("Diagonale, excentricité 5 mm", "N + M ELU", taux, 1.0, "taux")

    # --- Platine basse des potelets (platine_bas_ep) et aile du limon sous les 2 vis M8 (tronçon en T, effet de levier)
    c_ = potelet_l
    M_pot = 1.5 * q_gc * pas_potelets_v1 * (mc_h + limon_descente)
    T = M_pot / (platine_bas_b / 2) / 2   # comme predim.py
    B_t = 0.9 * fub * As_M8 / gM2
    m_pl = 100 / 2 - c_ / 2 - 0.8 * 3 * sqrt(2)   # vis à 50 mm de l'axe, cordon de 3 mm au pied du tube, supposé
    verif(f"Platine basse potelet {platine_bas_ep} mm (levier)", "traction ELU", T / 1e3,
          tstub(T, platine_bas_ep, m_pl, 15, platine_bas_b, B_t) / 1e3, "kN")
    m_ai = 36 - limon_tw / 2   # vis à ≈ 36 mm du dos de l'âme (CONCEPTION §7)
    verif("Aile du limon 12 mm sous vis M8", "traction ELU", T / 1e3,
          tstub(T, limon_tf, m_ai, limon_b - 36, 100 / 2, B_t) / 1e3, "kN")

    # --- Déversement de la poutre avant (UPE, L = largeur du palier, appuis à fourche), ailes libres, côté sécurité
    L = L_p
    Iz, J = p.upe_Iz, p.upe_J
    M_cr = 1.13 * pi**2 * E_acier * Iz / L**2 * sqrt(upe_Iw / Iz + L**2 * G_acier * J / (pi**2 * E_acier * Iz))
    lam = sqrt(upe_W * fy / M_cr)
    phi = 0.5 * (1 + 0.76 * (lam - 0.2) + lam**2)   # courbe d (h / b > 2)
    chi = min(1.0, 1 / (phi + sqrt(phi**2 - lam**2)))
    ef = limons_et_poutre_avant()
    M_ed = ef["M_pa"]
    verif(f"Poutre avant, déversement (L {L:.0f})", "flexion ELU", M_ed / 1e6, chi * upe_W * fy / gM1 / 1e6, "kN·m")
    # Limons : marches fixées à chaque giron, longueur libre ≈ pas_volee → déversement sans objet
    L = giron / cos(angle)
    M_cr_l = 1.13 * pi**2 * E_acier * Iz / L**2 * sqrt(upe_Iw / Iz + L**2 * G_acier * J / (pi**2 * E_acier * Iz))
    print(f"  Limons : longueur libre {L:.0f} mm entre marches, M_cr = {M_cr_l / 1e6:.0f} kN·m : pas de déversement")

    # --- Gauchissement de la poutre avant : couples R × e des 4 limons (appui sur le dos de l'âme, e = e0 - tw / 2),
    # appuis à fourche (rotation bloquée, gauchissement libre), différences finies
    e = e0 - limon_tw / 2
    R_v1, R_v2 = ef["R"]["V1"][0], ef["R"]["V2"][0]
    x_l = ef["x_limons"]
    n_ = 400
    x = np.linspace(0, L_p, n_ + 1)
    dx = x[1] - x[0]
    mt = np.zeros(n_ + 1)
    for xi, R in zip(x_l, (R_v1, R_v1, R_v2, R_v2)):
        mt[int(round(xi / dx))] += R * e / dx
    # E Iw θ'''' - G J θ'' = mt, θ = θ'' = 0 aux bouts
    A = np.zeros((n_ + 1, n_ + 1))
    bvec = mt.copy()
    for i in range(2, n_ - 1):
        A[i, i - 2:i + 3] = E_acier * upe_Iw * np.array([1, -4, 6, -4, 1]) / dx**4 \
            - G_acier * J * np.array([0, 1, -2, 1, 0]) / dx**2
    for i, j in ((0, 0), (n_, n_)):
        A[i, j], bvec[i] = 1, 0
    A[1, 0:3], bvec[1] = (1, -2, 1), 0
    A[n_ - 1, n_ - 2:n_ + 1], bvec[n_ - 1] = (1, -2, 1), 0
    theta = np.linalg.solve(A, bvec)
    B = -E_acier * upe_Iw * np.gradient(np.gradient(theta, dx), dx)
    sigma_w = np.max(np.abs(B)) * omega_max / upe_Iw
    sigma_b = M_ed / upe_W
    verif("Poutre avant, flexion + gauchissement", "contrainte ELU", sigma_b + sigma_w, sigma_lim, "MPa")

    # --- Couple de la poussée sur les poutres du palier : main courante à mc_palier_h du plancher ; poutre tenue en
    # torsion aux deux bouts (angles soudés), Saint-Venant seul (borne haute du cisaillement, gauchissement négligé)
    t = 1.5 * q_gc * (limon_h / 2 + palier_ep + mc_palier_h)
    for nom, L in (("arrière", L_p), ("latérales", palier_profondeur)):
        T = t * L / 2
        verif(f"Poutre {nom} palier, couple de la poussée", "torsion ELU", T * limon_tf / J, tau_lim, "MPa")

    # --- Vibrations : première fréquence propre sous G + 0,3 Q (ψ2 cat. A), poutre sur 2 appuis ; repère 5 Hz, supposé
    marche_g = g_chene * giron * marche_epaisseur * emmarchement + equerres_g
    for nom, L_h in (("V1", (nb_volee1 - 1) * giron), ("V2", nb_volee2 * giron)):
        L_s = L_h / cos(angle)
        w = (marche_g / 2 / giron + 0.3 * q_k * emmarchement / 2) * cos(angle) + upe_g + g_gc   # N/mm de limon
        f = pi / 2 * sqrt(E_acier * upe_I / (w / 9810 * L_s**4))
        verif(f"Limon {nom}, fréquence propre (L {L_s:.0f})", "≥ 5 Hz", 5, f, "Hz")
    # Palier : flèche de la poutre avant sous G + 0,3 Q et les réactions des limons, f ≈ 17,75 / √δ (δ en mm)
    _, d = poutre(L_p, w=g_chene * palier_ep * palier_profondeur / 2 + upe_g + 0.3 * q_k * palier_profondeur / 2,
                  charges=[(ef["R"][v][1], xi) for v, xi in zip(("V1", "V1", "V2", "V2"), x_l)], EI=E_acier * upe_I)
    verif("Poutre avant, fréquence propre", "≥ 5 Hz", 5, 17.75 / sqrt(d), "Hz")


if __name__ == "__main__":
    calculer()
    print(f"UPE 220 : e0 = {e0:.1f} mm de l'axe de l'âme, Iw = {upe_Iw / 1e9:.2f}e9 mm⁶, ω max = {omega_max:.0f} mm²")
    afficher()
    print("\nHypothèses : cordons de 5 mm (gousset) et de 3 mm (potelets, languettes), positions des vis et des boulons"
          " d'après CONCEPTION.md, rondelles Ø16 ; repère vibratoire 5 Hz."
          "\nNon calculé : paroi du pied sous le gousset, jarret de la poutre avant aux trous, plancher (couvert par la"
          " marche : même chêne 60 mm, portée ≤ 1 000 mm, charge mieux répartie).")

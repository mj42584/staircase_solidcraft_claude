"""Visualisation 3D du modèle en barres (PyVista) : moments fléchissants ELU et déformée ELS amplifiée.

Installer : pip install PyNiteFEA pyvista
Lancer : python3 calc/visu.py            → fenêtre 3D interactive
         python3 calc/visu.py --png DOSSIER  → moments.png et deformee.png dans DOSSIER
Sans écran (serveur) : xvfb-run -a python3 calc/visu.py --png DOSSIER
"""
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

from portique import construire

N_POINTS = 21
ECHELLE_DEFORMEE = 300


def repere(p):
    return np.array([p[0], p[2], p[1]])  # PyNite (Y vertical) → repère de CONCEPTION.md (Z vertical)


def barres(m, combo, echelle=0.0):
    """Une polyligne par barre : points (déformés × echelle) et moment |M| en kN·m à chaque point."""
    lignes = []
    for b in m.members.values():
        if b.section.name == "rigide":
            continue
        i, j = b.i_node, b.j_node
        x = np.linspace(0, b.L(), N_POINTS)
        t = x / b.L()
        Pi, Pj = np.array([i.X, i.Y, i.Z]), np.array([j.X, j.Y, j.Z])
        Di = np.array([i.DX[combo], i.DY[combo], i.DZ[combo]])
        Dj = np.array([j.DX[combo], j.DY[combo], j.DZ[combo]])
        ey, ez = b.T()[1, :3], b.T()[2, :3]  # axes locaux y et z en coordonnées globales
        dy = b.rel_deflection_array("dy", N_POINTS, combo)[1]
        dz = b.rel_deflection_array("dz", N_POINTS, combo)[1]
        pts = Pi + np.outer(t, Pj - Pi) + echelle * (np.outer(1 - t, Di) + np.outer(t, Dj)
                                                    + np.outer(dy, ey) + np.outer(dz, ez))
        M = np.hypot(b.moment_array("My", N_POINTS, combo)[1], b.moment_array("Mz", N_POINTS, combo)[1]) / 1e6
        ligne = pv.lines_from_points(np.array([repere(p) for p in pts]))
        ligne["M (kN·m)"] = M
        lignes.append(ligne)
    return pv.merge(lignes)


def appuis(m):
    return pv.PolyData(np.array([repere((n.X, n.Y, n.Z)) for n in m.nodes.values() if n.support_DY]))


def scene(p, m, titre, maillage, **options):
    p.add_text(titre, font_size=10)
    p.add_mesh(maillage, line_width=6, render_lines_as_tubes=True, **options)
    p.add_mesh(appuis(m), color="black", point_size=14, render_points_as_spheres=True)
    p.show_axes()
    p.enable_parallel_projection()
    p.view_vector((0.5, -1, 0.35))  # vue côté volée 1, légèrement plongeante


def main():
    m = construire()[0]
    moments = barres(m, "ELU_X")
    deformee = barres(m, "ELS_X", ECHELLE_DEFORMEE)
    initiale = barres(m, "ELS_X")
    titres = ("Moment fléchissant M, ELU_X (kN·m)", f"Déformée ELS_X × {ECHELLE_DEFORMEE}")

    def dessiner(p, k):
        if k == 0:
            scene(p, m, titres[0], moments, scalars="M (kN·m)", cmap="turbo")
        else:
            p.add_mesh(initiale, color="lightgray", line_width=2)
            scene(p, m, titres[1], deformee, color="tab:blue")

    if "--png" in sys.argv:
        dossier = Path(sys.argv[sys.argv.index("--png") + 1])
        dossier.mkdir(parents=True, exist_ok=True)
        for k, nom in enumerate(("moments.png", "deformee.png")):
            p = pv.Plotter(off_screen=True, window_size=(1400, 1000))
            dessiner(p, k)
            p.screenshot(dossier / nom)
            p.close()
    else:
        p = pv.Plotter(shape=(1, 2), window_size=(1800, 900))
        for k in (0, 1):
            p.subplot(0, k)
            dessiner(p, k)
        p.link_views()
        p.show()


if __name__ == "__main__":
    main()

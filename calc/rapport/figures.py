"""Figures du rapport de calcul (matplotlib) : schéma du modèle en barres et déformée sous la poussée en travers.

Lancer depuis calc/ : PYTHONPATH=. uv run --no-project --with PyNiteFEA==3.2 python3 rapport/figures.py
"""
from pathlib import Path

import matplotlib.pyplot as plt

from portique import construire

DOSSIER = Path(__file__).parent


def trace(ax, m, h, v, combo=None, ech=0.0, **style):
    """Barres projetées sur les axes (h, v) du repère de CONCEPTION.md ; déformée amplifiée de ech si combo."""
    def pt(n, axe):
        val = {"x": n.X, "y": n.Z, "z": n.Y}[axe]
        if combo:
            val += ech * {"x": n.DX, "y": n.DZ, "z": n.DY}[axe][combo]
        return val
    for b in m.members.values():
        ax.plot([pt(b.i_node, h), pt(b.j_node, h)], [pt(b.i_node, v), pt(b.j_node, v)], **style)


def appuis(ax, m, h, v):
    for n in m.nodes.values():
        if n.support_DX:
            fixe = n.support_RX and n.support_RY and n.support_RZ
            p = {"x": n.X, "y": n.Z, "z": n.Y}
            ax.plot(p[h], p[v], "ks" if fixe else "ko", ms=6, mfc="k" if fixe else "w")


m, _, _ = construire(False)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6))
for ax, (h, v), titre in ((a1, ("x", "y"), "Vue de dessus (X, Y)"), (a2, ("x", "z"), "Élévation côté V1 (X, Z)")):
    trace(ax, m, h, v, color="0.2", lw=1.5)
    appuis(ax, m, h, v)
    ax.set_title(titre)
    ax.set_xlabel(f"{h.upper()} (mm)")
    ax.set_ylabel(f"{v.upper()} (mm)")
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
a1.annotate("V1", (1900, -650), ha="center")
a1.annotate("V2", (2900, 650), ha="center")
a1.annotate("palier", (4336, 0), ha="center")
a2.plot([], [], "ks", label="encastrement")
a2.plot([], [], "ko", mfc="w", label="articulation")
a2.legend(loc="upper left", fontsize=8)
fig.tight_layout()
fig.savefig(DOSSIER / "modele.png", dpi=200)

ech = 1000
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
for ax, rigide in zip(axes, (True, False)):
    m, _, coins = construire(rigide)
    trace(ax, m, "y", "z", color="0.75", lw=1)
    trace(ax, m, "y", "z", "ELS_GCY", ech, color="tab:red", lw=1.5)
    appuis(ax, m, "y", "z")
    d = max(abs(m.nodes[n].DZ["ELS_GCY"]) for n in coins)
    ax.set_title(f"Tête des pieds {'rigide' if rigide else 'articulée'} : palier {d:.1f} mm".replace(".", ","))
    ax.set_xlabel("Y (mm)")
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
axes[0].set_ylabel("Z (mm)")
fig.suptitle(f"Vue de face (Y, Z), ELS poussée en travers, déformée × {ech} (en rouge)")
fig.tight_layout()
fig.savefig(DOSSIER / "deformee_travers.png", dpi=200)

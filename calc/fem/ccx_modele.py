"""Écriture et lancement d'un calcul CalculiX (.inp) : UPE en briques C3D20R, tubes et marches en poutres U1, liaisons
par corps rigides et équations. Outil commun à global_ccx.py et à ses contrôles (controles_ccx.py).

Constats sur CalculiX 2.23 (Flatpak FreeCAD 1.1), qui ont fixé ces choix :
- coques : *RIGID BODY refusé sur leurs nœuds, et jonction âme / aile d'un UPE trop souple (console : flèche +24 à
  +100 % selon le raccord) → UPE en volumes, une brique quadratique dans l'épaisseur ;
- poutre U1 : la direction donnée sous la section est l'axe local 1, I11 gouverne la flèche le long de cet axe ; la
  constante de torsion est IGNORÉE (CalculiX prend I11 + I22) : aucun profil ouvert en U1 ;
- poutre U1 et briques ne partagent pas de nœud : liaison par équations vers le nœud de référence (translations) et
  le nœud de rotation (rotations) d'un corps rigide.
"""
import math
import os
import re
import subprocess

import numpy as np

DOSSIER = os.path.expanduser("~/.var/app/org.freecad.FreeCAD/cache/verif")  # visible du CalculiX du Flatpak FreeCAD
CCX = ["flatpak", "run", "--command=ccx", "org.freecad.FreeCAD"]


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


class Modele:
    def __init__(self):
        self.nodes = []          # coordonnées, id = index + 1
        self.elsets = {}         # nom -> (type, [connectivités])
        self.solide = {}         # elset -> matériau
        self.beam = {}           # elset -> (A, I11, I22, n1, matériau)
        self.rigides = []        # (nœuds, ref, rot)
        self.equations = []      # [(nœud, ddl, coef), ...] ; le premier terme est le ddl dépendant
        self.appuis = []         # (nœud, ddl premier, ddl dernier)
        self.charges = {}        # cas -> {(nœud, ddl): valeur}
        self.sorties = {}        # nom -> liste de nœuds (U, RF imprimés)

    def noeud(self, p):
        self.nodes.append(np.asarray(p, float))
        return len(self.nodes)

    def element(self, elset, typ, conn):
        self.elsets.setdefault(elset, (typ, []))[1].append(tuple(conn))

    def charge(self, cas, n, ddl, v):
        d = self.charges.setdefault(cas, {})
        d[n, ddl] = d.get((n, ddl), 0.0) + v

    def poutre(self, elset, a, b, nb, section):
        """Poutre U1 de a à b (nœuds existants ou points), nb éléments ; section (A, I11, I22, n1, matériau)."""
        pa = self.nodes[a - 1] if isinstance(a, int) else np.asarray(a, float)
        pb = self.nodes[b - 1] if isinstance(b, int) else np.asarray(b, float)
        ns = [a if isinstance(a, int) else self.noeud(pa)]
        for i in range(1, nb):
            ns.append(self.noeud(pa + (pb - pa) * i / nb))
        ns.append(b if isinstance(b, int) else self.noeud(pb))
        for i in range(nb):
            self.element(elset, "U1", (ns[i], ns[i + 1]))
        self.beam[elset] = section
        return ns

    def rigide(self, noeuds, p_ref):
        """Corps rigide sur des nœuds de briques ; renvoie (ref, rot) : translations du point p_ref, rotations."""
        ref, rot = self.noeud(p_ref), self.noeud(p_ref)
        self.rigides.append((sorted(set(noeuds)), ref, rot))
        return ref, rot

    def lier(self, a, b, ddls=(1, 2, 3)):
        """ddl de a = ddl de b (a dépendant)."""
        for d in ddls:
            self.equations.append([(a, d, 1.0), (b, d, -1.0)])

    def attacher(self, n_poutre, ref, rot, rotations=(4, 5, 6)):
        """Nœud de poutre U1 lié à un corps rigide : translations de ref, et les rotations listées de rot."""
        self.lier(n_poutre, ref)
        for d in rotations:
            self.equations.append([(n_poutre, d, 1.0), (rot, d - 3, -1.0)])

    def lier_rotation(self, a, ddl_a, b, ddl_b, axe):
        """Rotation autour de axe égale : sum axe_i (r_a,i - r_b,i) = 0 ; ddl_a / ddl_b = premier ddl de rotation."""
        axe = unit(axe)
        i0 = int(np.argmax(np.abs(axe)))
        ordre = [i0] + [i for i in range(3) if i != i0]
        termes = []
        for i in ordre:
            if abs(axe[i]) > 1e-9:
                termes.append((a, ddl_a + i, axe[i]))
        termes += [(b, ddl_b + i, -axe[i]) for i in range(3) if abs(axe[i]) > 1e-9]
        self.equations.append(termes)

    def ecrire(self, nom, cas, frd=True):
        lignes = ["*NODE, NSET=NALL"] + [f"{i},{p[0]:.4f},{p[1]:.4f},{p[2]:.4f}" for i, p in enumerate(self.nodes, 1)]
        # déclaration exigée de l'élément U1 (CalculiX signale la ligne des ddl comme illisible, sans conséquence)
        lignes += ["*USER ELEMENT,TYPE=U1,INTEGRATION POINTS=2,MAXDOF=6,NODES=2", "1,2,3,4,5,6"]
        eid = 0
        for es, (typ, conns) in self.elsets.items():
            lignes.append(f"*ELEMENT,TYPE={typ},ELSET={es}")
            for c in conns:
                eid += 1
                cs = [str(eid)] + list(map(str, c))
                for i in range(0, len(cs), 16):  # lignes de 16 entrées au plus
                    lignes.append(",".join(cs[i:i + 16]) + ("," if i + 16 < len(cs) else ""))
        lignes += ["*MATERIAL,NAME=ACIER", "*ELASTIC", "210000,0.3", "*MATERIAL,NAME=CHENE", "*ELASTIC", "11000,0.3"]
        for es, mat in self.solide.items():
            lignes += [f"*SOLID SECTION,ELSET={es},MATERIAL={mat}"]
        for es, (A, I11, I22, n1, mat) in self.beam.items():
            lignes += [f"*BEAM GENERAL SECTION,ELSET={es},MATERIAL={mat},SECTION=GENERAL",
                       f"{A:.6g},{I11:.6g},0,{I22:.6g},{I11 + I22:.6g}", f"{n1[0]:.6f},{n1[1]:.6f},{n1[2]:.6f}"]
        for k, (ns, ref, rot) in enumerate(self.rigides):
            lignes.append(f"*NSET,NSET=RB{k}")
            lignes += [",".join(map(str, ns[i:i + 12])) for i in range(0, len(ns), 12)]
            lignes.append(f"*RIGID BODY,NSET=RB{k},REF NODE={ref},ROT NODE={rot}")
        if self.equations:
            lignes.append("*EQUATION")
            for t in self.equations:
                lignes.append(str(len(t)))
                lignes.append(",".join(f"{n},{d},{c:.9g}" for n, d, c in t))
        lignes.append("*BOUNDARY")
        lignes += [f"{n},{a},{b}" for n, a, b in self.appuis]
        tous = sorted({n for ns in self.sorties.values() for n in ns})
        lignes.append("*NSET,NSET=NSORT")
        lignes += [",".join(map(str, tous[i:i + 12])) for i in range(0, len(tous), 12)]
        poutres = [es for es, (typ, _) in self.elsets.items() if typ == "U1"]
        for c in cas:
            lignes += ["*STEP", "*STATIC", "*CLOAD,OP=NEW"]
            lignes += [f"{n},{d},{v:.6g}" for (n, d), v in self.charges.get(c, {}).items() if v]
            lignes += ["*NODE PRINT,NSET=NSORT", "U,RF"]
            for es in poutres:
                lignes += [f"*EL PRINT,ELSET={es}", "S"]
            if frd:
                lignes += ["*NODE FILE", "U", "*EL FILE", "S"]
            lignes.append("*END STEP")
        os.makedirs(DOSSIER, exist_ok=True)
        with open(os.path.join(DOSSIER, nom + ".inp"), "w") as f:
            f.write("\n".join(lignes) + "\n")

    def lancer(self, nom):
        r = subprocess.run(CCX + ["-i", nom], cwd=DOSSIER, capture_output=True, text=True)
        if "ERROR" in r.stdout or r.returncode:
            raise RuntimeError(r.stdout[-3000:])
        return lire_dat(os.path.join(DOSSIER, nom + ".dat"))


def lire_dat(chemin):
    """{pas: {"U": {n: [...]}, "RF": {n: [3]}, "S": {elset: [(e, ip, 6 valeurs)]}}}"""
    res, pas, bloc, es = {}, 0, None, None
    for l in open(chemin):
        if "S T E P" in l:
            pas = int(l.split()[-1])
            res.setdefault(pas, {"U": {}, "RF": {}, "S": {}})
            bloc = None
            continue
        m = re.match(r"\s*(displacements|forces|stresses).*?set (\S+) and time", l)
        if m:
            bloc, es = {"displacements": "U", "forces": "RF", "stresses": "S"}[m.group(1)], m.group(2)
            continue
        v = l.split()
        if not v or bloc is None:
            continue
        try:
            nums = [float(x) for x in v]
        except ValueError:
            bloc = None
            continue
        if bloc == "S":
            res[pas]["S"].setdefault(es, []).append((int(nums[0]), int(nums[1]), nums[2:]))
        else:
            res[pas][bloc][int(nums[0])] = nums[1:]
    return res


def lire_frd(chemin):
    """Coordonnées et, par pas, contraintes (n, 6) et déplacements (n, 3) nodaux : (ids, xyz, [S], [U])."""
    xyz, S, U, cur, mode = {}, [], [], None, None
    with open(chemin) as f:
        for l in f:
            if l.startswith("    2C"):
                mode = "nodes"
            elif l.startswith(" -4  STRESS"):
                mode, cur = "S", {}
            elif l.startswith(" -4  DISP"):
                mode, cur = "U", {}
            elif l.startswith(" -4"):
                mode = None
            elif l.startswith(" -3"):
                if mode in ("S", "U"):
                    (S if mode == "S" else U).append(cur)
                mode = None
            elif l.startswith(" -1") and mode:
                n = int(l[3:13])
                vals = [float(l[13 + 12 * i:25 + 12 * i]) for i in range((len(l.rstrip()) - 13) // 12)]
                (xyz if mode == "nodes" else cur)[n] = vals
    ids = np.array(sorted(S[-1] if S else xyz))
    return (ids, np.array([xyz[i] for i in ids]), [np.array([s.get(i, [0.0] * 6) for i in ids]) for s in S],
            [np.array([u.get(i, [0.0] * 3)[:3] for i in ids]) for u in U])


def von_mises(s):
    sxx, syy, szz, sxy, syz, szx = np.asarray(s).T
    return np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2) + 3 * (sxy**2 + syz**2 + szx**2))


class Upe:
    """UPE en briques C3D20R. Repère local : s le long de u, y' le long de w depuis le dos de l'âme (y' = 0) vers le bout
    des ailes (y' = b), z' le long de n depuis la mi-hauteur. origine = dos de l'âme à mi-hauteur, s de s0 à s1."""

    def __init__(self, m, nom, origine, u, n, w, s0, s1, h, b, tw, tf, dx=40.0, nw=6, nf=3):
        self.m, self.nom = m, nom
        self.o, self.u, self.n, self.w = np.asarray(origine, float), unit(u), unit(n), unit(w)
        self.h, self.b, self.tw, self.tf = h, b, tw, tf
        ns = max(2, math.ceil((s1 - s0) / dx))
        self.s = np.linspace(s0, s1, ns + 1)
        zs_ame = np.linspace(-h / 2 + tf, h / 2 - tf, nw + 1)
        ys_aile = np.concatenate(([0.0], np.linspace(tw, b, nf + 1)))
        # quadrilatères de la section (y'0, y'1, z'0, z'1)
        quads = [(0.0, tw, zs_ame[k], zs_ame[k + 1]) for k in range(nw)]
        for z0, z1 in ((h / 2 - tf, h / 2), (-h / 2, -h / 2 + tf)):
            quads += [(ys_aile[j], ys_aile[j + 1], z0, z1) for j in range(nf + 1)]
        self.cle = {}            # (s, y', z') arrondis -> nœud
        self.loc = {}            # nœud -> (s, y', z')
        sens = np.dot(np.cross(self.u, self.w), self.n) > 0
        for i in range(ns):
            sa, sb = self.s[i], self.s[i + 1]
            for y0, y1, z0, z1 in quads:
                c = [(sa, y0, z0), (sb, y0, z0), (sb, y1, z0), (sa, y1, z0),
                     (sa, y0, z1), (sb, y0, z1), (sb, y1, z1), (sa, y1, z1)]
                if not sens:  # repère local indirect : on retourne la brique
                    c = [c[0], c[3], c[2], c[1], c[4], c[7], c[6], c[5]]
                aretes = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
                pts = c + [tuple((np.array(c[a]) + np.array(c[b_])) / 2) for a, b_ in aretes]
                m.element(f"{nom}", "C3D20R", [self._noeud(p) for p in pts])
        m.solide[nom] = "ACIER"

    def _noeud(self, p):
        k = tuple(round(x, 4) for x in p)
        if k not in self.cle:
            self.cle[k] = self.m.noeud(self.point(*p))
            self.loc[self.cle[k]] = p
        return self.cle[k]

    def point(self, s, y, z):
        return self.o + s * self.u + y * self.w + z * self.n

    def zone(self, filtre):
        """Nœuds dont les coordonnées locales (s, y', z') vérifient filtre."""
        return [n for n, (s, y, z) in self.loc.items() if filtre(s, y, z)]

    def section(self, s):
        return self.zone(lambda s_, y, z: abs(s_ - s) < 1e-6)

    def ligne(self, cas, filtre, w_vec):
        """Charge linéique w_vec (N/mm, vecteur global) sur les nœuds retenus par filtre, au prorata de la longueur."""
        par_s = {}
        for n, (s, y, z) in self.loc.items():
            if filtre(s, y, z):
                par_s.setdefault(round(s, 4), []).append(n)
        ss = sorted(par_s)
        for i, s in enumerate(ss):
            a = (ss[i - 1] + s) / 2 if i else s
            b_ = (s + ss[i + 1]) / 2 if i < len(ss) - 1 else s
            for n in par_s[s]:
                for d in range(3):
                    if w_vec[d]:
                        self.m.charge(cas, n, d + 1, w_vec[d] * (b_ - a) / len(par_s[s]))

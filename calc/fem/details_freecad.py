"""Détails en volumique dans l'atelier FEM de FreeCAD (Gmsh, tétraèdres du 2e ordre, CalculiX) : marche en chêne sur ses
cornières, gousset de diagonale, platine basse de potelet (contact sur l'aile du limon). Chaque détail est une analyse
FEM dans le document FreeCAD « Verification_FEM », que l'on peut rouvrir et relancer dans l'atelier FEM.

Lancé dans FreeCAD (console Python ou serveur MCP) : exec(open(".../calc/fem/details_freecad.py").read())
Valeurs comparées : predim.py et assemblages.py (recopiées ici, en tête de chaque détail).
"""
import math
import os

import sys

import FreeCAD as App
import ObjectsFem
import Part
from BOPTools import SplitAPI
from FreeCAD import Vector as V
from femmesh.gmshtools import GmshTools
from femtools import ccxtools

sys.path.insert(0, "/home/mj/Documents/Escalier gab/Escalier gab/calc/fem")  # shortcut: chemin du dépôt en dur
from ccx_modele import lire_dat, lire_frd  # noqa: E402

DOSSIER = os.path.expanduser("~/.var/app/org.freecad.FreeCAD/cache/verif")
DOC = "Verification_FEM"
DETAILS = globals().get("DETAILS", ("marche", "gousset", "platine"))  # à définir avant exec() pour n'en lancer qu'une partie
doc = App.newDocument(DOC)
BILAN = {}


def feature(nom, forme):
    o = doc.getObject(nom) or doc.addObject("Part::Feature", nom)
    o.Shape = forme
    return o


def faces_ou(obj, test):
    return [f"Face{i}" for i, f in enumerate(obj.Shape.Faces, 1) if test(f)]


def force(nom, obj, faces, newtons, axe):
    """Force répartie sur des faces, dans la direction d'un axe global (vecteur unitaire) : FreeCAD prend la
    direction d'une arête de référence (DirectionVector seul est écrasé au recalcul) ; le sens est vérifié."""
    F = ObjectsFem.makeConstraintForce(doc, nom)
    F.References = [(obj, f) for f in faces]
    F.Force = f"{newtons} N"
    a = V(*axe)
    arete = next(f"Edge{i}" for i, e in enumerate(obj.Shape.Edges, 1)
                 if e.Curve.__class__.__name__ == "Line" and abs(abs(e.Curve.Direction.dot(a)) - 1) < 1e-9)
    F.Direction = (obj, [arete])
    doc.recompute()
    if F.DirectionVector.dot(a) < 0:
        F.Reversed = not F.Reversed
        doc.recompute()
    assert (F.DirectionVector - a).Length < 1e-6, (nom, F.DirectionVector, a)
    return F


def materiau(nom, E, nu, rho, refs=None):
    m = ObjectsFem.makeMaterialSolid(doc, nom)
    m.Material = {"Name": nom, "YoungsModulus": f"{E} MPa", "PoissonRatio": str(nu), "Density": f"{rho} kg/m^3"}
    if refs:
        m.References = refs
    return m


def analyse(nom, obj, objets, taille, contact=False, reactions=()):
    """Maille obj (Gmsh, 2e ordre), lance CalculiX ; renvoie (analyse, résultat, chemin du .dat)."""
    for o in list(doc.Objects):  # relance propre : on retire l'analyse précédente du même nom
        if o.Name.startswith(f"Analyse_{nom}"):
            for c in o.Group:
                doc.removeObject(c.Name)
            doc.removeObject(o.Name)
    an = ObjectsFem.makeAnalysis(doc, f"Analyse_{nom}")
    sol = ObjectsFem.makeSolverCalculiXCcxTools(doc, f"CalculiX_{nom}")
    sol.WorkingDir = os.path.join(DOSSIER, nom)
    if contact:
        sol.GeometricalNonlinearity = "linear"
        sol.IncrementsMaximum = 200
    os.makedirs(sol.WorkingDir, exist_ok=True)
    an.addObject(sol)
    for o in objets:
        an.addObject(o)
    mesh = ObjectsFem.makeMeshGmsh(doc, f"Maillage_{nom}")
    mesh.Shape = obj
    mesh.CharacteristicLengthMax = taille
    mesh.ElementOrder = "2nd"
    mesh.CoherenceMesh = not contact  # contact : nœuds distincts de part et d'autre
    an.addObject(mesh)
    doc.recompute()  # tables de charges nodales des contraintes à jour
    err = GmshTools(mesh).create_mesh()
    if err:
        raise RuntimeError(err)
    fea = ccxtools.FemToolsCcx(an, sol)
    fea.update_objects()
    fea.setup_working_dir(sol.WorkingDir)
    msg = fea.check_prerequisites()
    if msg:
        raise RuntimeError(msg)
    fea.write_inp_file()
    corriger_noeuds_rigides(fea.inp_file_name, an, mesh)
    if reactions:  # réactions nœud par nœud des ensembles demandés (FreeCAD n'écrit que leurs totaux)
        txt = open(fea.inp_file_name).read()
        ajout = "".join(f"*NODE PRINT, NSET={r}\nRF\n" for r in reactions)
        i = txt.rindex("*END STEP")
        open(fea.inp_file_name, "w").write(txt[:i] + ajout + txt[i:])
    fea.ccx_run()
    # résultats lus dans le .frd : leur chargement par FreeCAD (load_results) dépasse 10 min sans interface
    base = fea.inp_file_name[:-4]
    if not os.path.exists(base + ".frd"):
        raise RuntimeError(f"{nom} : pas de résultat (voir {sol.WorkingDir})")
    return an, base + ".frd", base + ".dat", mesh


def corriger_noeuds_rigides(inp, an, mesh):
    """FreeCAD 1.1 numérote les nœuds de référence d'un corps rigide NodeCount + 2 i + 1 : avec la numérotation de
    Gmsh, ces numéros existent déjà dans le maillage (constaté : un élément de la platine étiré jusqu'au nœud de
    référence). On les renumérote après le plus grand nœud, dans la partie du fichier qui suit les corps rigides."""
    rbs = [o for o in an.Group if o.isDerivedFrom("Fem::ConstraintRigidBody")]
    if not rbs:
        return
    import re
    txt = open(inp).read()
    i = txt.index("** Rigid Body Constraints")
    tete, queue = txt[:i], txt[i:]
    n_max = max(mesh.FemMesh.Nodes)
    nc = mesh.FemMesh.NodeCount
    for k, rb in enumerate(rbs):
        idx = an.Group.index(rb)
        for vieux, neuf in ((nc + 2 * idx + 1, n_max + 2 * k + 1), (nc + 2 * idx + 2, n_max + 2 * k + 2)):
            queue = re.sub(rf"\b{vieux}\b", str(neuf), queue)
    open(inp, "w").write(tete + queue)


def noeuds_et_contraintes(frd):
    """[(x, y, z, sxx, syy, szz, sxy, sxz, syz, ux, uy, uz)] par nœud, dernier incrément du .frd."""
    ids, P, S, U = lire_frd(frd)
    s, u = S[-1], U[-1]  # ordre du .frd : SXX SYY SZZ SXY SYZ SZX
    return [(*P[k], s[k, 0], s[k, 1], s[k, 2], s[k, 3], s[k, 5], s[k, 4], *u[k]) for k in range(len(ids))]


def totaux_rf(dat):
    """Totaux des réactions par ensemble de nœuds (*NODE PRINT TOTALS=ONLY) du dernier incrément : {SET: (fx, fy, fz)}."""
    tot, nom = {}, None
    for l in open(dat):
        if "total force (fx,fy,fz) for set" in l:
            nom = l.split("for set")[1].split()[0]
            continue
        v = l.split()
        if nom and len(v) == 3:
            tot[nom] = tuple(float(x) for x in v)
            nom = None
    return tot


# =====================================================================================================================
# 1. Marche en chêne 274 × 1000 × 60 sur les ailes horizontales des cornières (200 × 50 à chaque bout), appui simple ;
#    charge ponctuelle Q = 2 kN sur 50 × 50 au milieu (EN 1991-1-1) + poids propre. predim.py : poutre de 1000 mm
#    sur 2 appuis, Q ponctuel sur toute la largeur → σ ELU 4,69 MPa, flèche ELS 0,80 mm.
#    Chêne isotrope (E = 11 000 MPa, ν = 0,3, comme predim.py) : le bois réel est orthotrope (E⊥ et G bien plus
#    faibles) — la répartition sur la largeur et la flèche d'effort tranchant sont donc sous-estimées.
# =====================================================================================================================
if "marche" in DETAILS:
    gi, L, ep, Qk = 274.0, 1000.0, 60.0, 2000.0
    bloc = Part.makeBox(gi, L, ep)
    plans = []
    for x in ((gi - 200) / 2, (gi + 200) / 2, gi / 2 - 25, gi / 2 + 25):
        plans.append(Part.makePlane(2000, 2000, V(x, -500, -500), V(1, 0, 0)))
    for y in (25, L - 25, 50, L - 50, L / 2 - 25, L / 2 + 25):
        plans.append(Part.makePlane(2000, 2000, V(-500, y, -500), V(0, 1, 0)))
    marche = feature("Marche", SplitAPI.slice(bloc, plans, "CompSolid"))
    # appui simple : ligne au milieu de l'aile horizontale de chaque cornière (y = 25 et L - 25)
    appuis = [f"Edge{i}" for i, e in enumerate(marche.Shape.Edges, 1)
              if abs(e.BoundBox.ZMax) < 1e-6 and e.BoundBox.YLength < 1e-6 and abs(e.BoundBox.YMin - 25) < 1e-6
              or abs(e.BoundBox.ZMax) < 1e-6 and e.BoundBox.YLength < 1e-6 and abs(e.BoundBox.YMin - (L - 25)) < 1e-6
              and abs(e.CenterOfMass.x - gi / 2) < 100]
    appuis = [a for a in appuis if abs(marche.Shape.getElement(a).CenterOfMass.x - gi / 2) < 100]
    charge = faces_ou(marche, lambda f: abs(f.CenterOfMass.z - ep) < 1e-6 and abs(f.CenterOfMass.x - gi / 2) < 25
                      and abs(f.CenterOfMass.y - L / 2) < 25)
    longueur = sum(marche.Shape.getElement(a).Length for a in appuis)
    # shortcut: lignes d'appui sur toute la largeur de la marche (274 mm) au lieu des 200 mm de la cornière
    assert abs(longueur - 2 * gi) < 1e-6 and len(charge) == 1, (appuis, longueur, charge)

    resultats_marche = {}
    for etat, fQ, fG in (("ELU", 1.5, 1.35), ("ELS", 1.0, 1.0)):
        objs = [materiau(f"Chene_{etat}", 11000, 0.3, 750)]
        ap = ObjectsFem.makeConstraintDisplacement(doc, f"Appuis_marche_{etat}")
        ap.References = [(marche, f) for f in appuis]
        ap.zFree, ap.zDisplacement = False, 0.0
        # une translation horizontale et une rotation tenues sans effort : nœuds d'un bout bloqués en x et y
        bout = ObjectsFem.makeConstraintDisplacement(doc, f"Tenue_marche_{etat}")
        bout.References = [(marche, appuis[0])]
        bout.xFree, bout.yFree = False, False
        F = ObjectsFem.makeConstraintForce(doc, f"Q_marche_{etat}")
        F.References = [(marche, charge[0])]
        F.Force = f"{fQ * Qk} N"
        F.DirectionVector = V(0, 0, -1)
        pp = ObjectsFem.makeConstraintSelfWeight(doc, f"Poids_marche_{etat}")
        pp.GravityAcceleration = f"{9810 * fG} mm/s^2"
        objs += [ap, bout, F, pp]
        an, res, dat, _ = analyse(f"marche_{etat}", marche, objs, 12.0)
        ns = noeuds_et_contraintes(res)
        resultats_marche[etat] = (max(abs(n[4]) for n in ns), max(abs(n[11]) for n in ns),
                                  sum(n[4] for n in ns if abs(n[2]) < 1e-6 and abs(n[1] - L / 2) < 1) /
                                  max(1, sum(1 for n in ns if abs(n[2]) < 1e-6 and abs(n[1] - L / 2) < 1)))
    s_elu, _, s_moy = resultats_marche["ELU"]
    _, f_els, _ = resultats_marche["ELS"]
    BILAN["Marche chêne, contrainte de flexion ELU maxi (MPa)"] = (4.69, s_elu)
    BILAN["Marche chêne, flèche ELS (mm)"] = (0.80, f_els)

# =====================================================================================================================
# 2. Gousset 120 × 120 × 10 soudé sur la face du pied (bord y = 0 encastré), trou Ø14 à 70 mm de la face et à
#    mi-hauteur ; effort de la diagonale N = 8,72 kN (assemblages.py, enveloppe PyNite) à 45,6° sur l'horizontale,
#    réparti sur la paroi du trou. assemblages.py : cordons a = 3,5 des deux côtés, traction + flexion du groupe de
#    cordons (excentricité 70 mm) → contrainte équivalente 48,70 MPa (limite fu / (βw γM2) = 360 MPa).
# =====================================================================================================================
if "gousset" in DETAILS:
    N_d, th, a_w = 8720.0, math.radians(45.6), 3.5
    plaque = Part.makeBox(10, 120, 120, V(-5, 0, 0)).cut(Part.makeCylinder(7, 20, V(-10, 70, 60), V(1, 0, 0)))
    gousset = feature("Gousset", plaque)
    soude = faces_ou(gousset, lambda f: abs(f.CenterOfMass.y) < 1e-6)
    trou = faces_ou(gousset, lambda f: not f.Surface.__class__.__name__.startswith("Plane"))
    enc = ObjectsFem.makeConstraintFixed(doc, "Soudure_gousset")
    enc.References = [(gousset, f) for f in soude]
    Fy = force("Effort_diagonale_Y", gousset, trou, N_d * math.cos(th), (0, 1, 0))
    Fz = force("Effort_diagonale_Z", gousset, trou, N_d * math.sin(th), (0, 0, 1))
    an, res, dat, _ = analyse("gousset", gousset, [materiau("Acier_gousset", 210000, 0.3, 7850), enc, Fy, Fz], 2.5,
                              reactions=[enc.Name])
    ns = noeuds_et_contraintes(res)
    ids, P, _, _ = lire_frd(res)
    xyz = dict(zip(ids.tolist(), P.tolist()))
    rf = lire_dat(dat)[1]["RF"]
    # efforts linéiques transmis par la soudure : réactions des nœuds du bord encastré, par tranches de 10 mm
    n_l, v_l = {}, {}
    for n, (fx, fy, fz) in rf.items():
        k = min(11, int(xyz[n][2] // 10))
        n_l[k] = n_l.get(k, 0.0) - fy / 10
        v_l[k] = v_l.get(k, 0.0) - fz / 10
    Fh = sum(n_l.values()) * 10
    w_max = 0.0
    for k in n_l:
        s_perp = n_l[k] / (2 * a_w) / math.sqrt(2)
        w_max = max(w_max, math.sqrt(s_perp**2 + 3 * (s_perp**2 + (v_l[k] / (2 * a_w)) ** 2)))
    BILAN["Soudure gousset / pied, contrainte équivalente ELU (MPa)"] = (48.70, w_max)
    BILAN["Gousset : effort normal transmis par la soudure, contrôle (kN)"] = (N_d * math.cos(th) / 1e3, abs(Fh) / 1e3)
    BILAN["Gousset : effort tangent transmis par la soudure, contrôle (kN)"] = (N_d * math.sin(th) / 1e3, abs(sum(v_l.values())) * 10 / 1e3)
    vm = [math.sqrt(0.5 * ((a - b) ** 2 + (b - c) ** 2 + (c - a) ** 2) + 3 * (d**2 + e**2 + f**2))
          for _, _, _, a, b, c, d, e, f, *_ in ns]
    BILAN["Gousset, von Mises maxi ELU (MPa, bord du trou compris)"] = (235.0, max(vm))

# =====================================================================================================================
# 3. Platine basse de potelet 130 × 50 × 10 sur l'aile du limon (bloc rigide, contact sans frottement), 2 vis M8 dans
#    l'axe à ± 50 mm (rondelles encastrées : vis infiniment raide), tube 40 × 40 × 3 soudé ; poussée ELU sur la main
#    courante 1,5 × 0,6 × 1052 = 947 N à 930 mm au-dessus de l'aile (potelet V1, predim.py). predim.py : traction par
#    vis M / (b / 2) / 2 = 17,61 kN (résistance 21,08 kN) ; assemblages.py : tronçon en T (levier) 84 %.
# =====================================================================================================================
if "platine" in DETAILS:
    F_p, h_p = 1.5 * 0.6 * 1052, 930.0
    pl = Part.makeBox(130, 50, 10, V(-65, -25, 0))
    for x in (-50, 50):
        pl = pl.cut(Part.makeCylinder(4.5, 30, V(x, 0, -5)))
        pl = pl.fuse(Part.makeCylinder(8, 2, V(x, 0, 10)).cut(Part.makeCylinder(4.5, 2, V(x, 0, 10))))
    tube = Part.makeBox(40, 40, 100, V(-20, -20, 10)).cut(Part.makeBox(34, 34, 100, V(-17, -17, 10)))
    pl = pl.fuse(tube).removeSplitter()
    aile = Part.makeBox(160, 85, 12, V(-80, -42.5, -12))
    ens = feature("Platine_potelet", Part.makeCompound([pl, aile]))
    dessous = faces_ou(ens, lambda f: abs(f.CenterOfMass.z) < 1e-6 and f.Area < 130 * 50 + 1)
    dessus_aile = faces_ou(ens, lambda f: abs(f.CenterOfMass.z) < 1e-6 and f.Area > 160 * 85 - 1)
    sol = faces_ou(ens, lambda f: abs(f.CenterOfMass.z + 12) < 1e-6)
    rond = {x: faces_ou(ens, lambda f, x=x: abs(f.CenterOfMass.z - 12) < 1e-6 and abs(f.CenterOfMass.x - x) < 1) for x in (-50, 50)}
    haut = faces_ou(ens, lambda f: abs(f.CenterOfMass.z - 110) < 1e-6)
    assert len(dessous) == 1 and len(dessus_aile) == 1 and len(sol) == 1 and all(len(v) == 1 for v in rond.values()), \
        (dessous, dessus_aile, sol, rond)
    objs = [materiau("Acier_platine", 210000, 0.3, 7850)]
    c = ObjectsFem.makeConstraintContact(doc, "Contact_platine_aile")
    c.References = [(ens, dessous[0]), (ens, dessus_aile[0])]
    c.Slope = "1e6 MPa/mm"
    e_sol = ObjectsFem.makeConstraintFixed(doc, "Aile_fixe")
    e_sol.References = [(ens, sol[0])]
    vis = []
    for x in (-50, 50):
        # tête de vis : bloquée en Z (traction de la vis) et en Y (cisaillement) ; en X sur une seule vis, sinon
        # les deux têtes fixes tendent la platine entre elles (±7 kN constatés avec des têtes encastrées)
        v_ = ObjectsFem.makeConstraintDisplacement(doc, f"Vis_{'gauche' if x < 0 else 'droite'}")
        v_.References = [(ens, rond[x][0])]
        v_.zFree, v_.yFree, v_.xFree = False, False, x > 0
        vis.append(v_)
    rb = ObjectsFem.makeConstraintRigidBody(doc, "Main_courante")
    rb.References = [(ens, f) for f in haut]
    rb.ReferenceNode = V(0, 0, h_p)
    rb.TranslationalModeY = "Load"
    rb.ForceY = f"{F_p} N"
    objs += [c, e_sol, *vis, rb]
    an, res, dat, _ = analyse("platine", ens, objs, 3.0, contact=True)
    tot = totaux_rf(dat)
    T = [abs(tot[v_.Name.upper()][2]) for v_ in vis]
    BILAN["Vis M8 la plus tendue, platine de potelet V1 (kN)"] = (17.61, max(T) / 1e3)
    ns = noeuds_et_contraintes(res)
    vm = [math.sqrt(0.5 * ((a - b) ** 2 + (b - c_) ** 2 + (c_ - a) ** 2) + 3 * (d**2 + e**2 + f**2))
          for x, y, z, a, b, c_, d, e, f, *_ in ns if 0 <= z <= 10 and abs(x) <= 65 and abs(y) <= 25]
    BILAN["Platine basse 10 mm, von Mises maxi élastique (MPa)"] = (235.0, max(vm))

doc.recompute()

doc.saveAs(os.path.join(DOSSIER, DOC + ".FCStd"))
print("\nBILAN (valeur des scripts, valeur FEM) :")
for k, (a, b) in BILAN.items():
    print(f"  {k:70} {a:9.2f} {b:9.2f}")

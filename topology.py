"""
topology.py
-----------
Topological features of a photo using PERSISTENT HOMOLOGY (topological data
analysis). Written in plain NumPy (no extra library), so it runs on Windows,
on Streamlit Cloud and here in exactly the same way.

Idea
----
Treat one colour channel of the photo as a height function f on a grid of
pixels (for example f = a*, the redness). For every level t we look at the
SUBLEVEL SET

        X_t = { pixels p : f(p) <= t }.

As t increases from min(f) to max(f) we get a nested family of sets
(a FILTRATION)  X_t1 ⊆ X_t2 ⊆ ...  and we record when topological features
appear ("birth") and disappear ("death"):

  H0 (dimension 0): connected components ("islands") of X_t
  H1 (dimension 1): holes ("rings")  enclosed by X_t

A feature born at b and dying at d has PERSISTENCE (lifetime) d - b.
Long-lived features are real structure (a patch, an ulcer border); short-lived
ones are noise. The list of (b, d) pairs is the PERSISTENCE DIAGRAM.
The number of features alive at level t is the BETTI NUMBER beta_k(t).

How it is computed
------------------
H0: process pixels in increasing order of f and merge neighbouring pixels with
    a union-find structure. When two components meet, the YOUNGER one (larger
    birth value) dies: this is the "elder rule". 8-neighbour connectivity is
    used (pixels are closed squares that touch at corners).
H1: by Alexander duality on the plane, a hole of X_t is a bounded component
    of the complement { f > t }. So H1 of the sublevel filtration is H0 of the
    SUPERLEVEL filtration of the complement, using the dual 4-neighbour
    connectivity, with all border pixels attached to the unbounded "outside".
These results were checked against the GUDHI library (CubicalComplex) on
random images: identical diagrams (see test_topology.py).

Features (summaries of each persistence diagram)
------------------------------------------------
  n_sig  : number of features with persistence > TAU   (significant features)
  total  : total persistence  sum_i (d_i - b_i)
  entropy: persistence entropy  E = - sum_i (l_i / L) log(l_i / L),
           l_i = d_i - b_i,  L = sum_i l_i
for 2 channels (a* = redness, L* = lightness) x 2 dimensions (H0, H1)
= 12 numbers per photo.
"""

import numpy as np

GRID = 64          # the photo is resized to 64 x 64 pixels before topology
TAU = 2.0          # persistence above this (in CIELAB units) counts as significant

_N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
_N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _find(parent, i):
    """Find the root of i in the union-find forest (with path halving)."""
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def _h0_sublevel(f: np.ndarray, neighbours, outside: bool = False) -> list:
    """0-dimensional persistence of the sublevel filtration of f.

    Returns a list of finite (birth, death) pairs. The oldest component never
    dies (essential class) and is not returned. If outside=True, an extra node
    with value -infinity is connected to every border pixel (used for H1)."""
    h, w = f.shape
    n = h * w
    flat = f.ravel()
    order = np.argsort(flat, kind="stable")
    parent = list(range(n + 1))
    birth = list(flat) + [-np.inf]          # node n = the outside
    active = [False] * n
    pairs = []

    def union(i, j, value):
        ri, rj = _find(parent, i), _find(parent, j)
        if ri == rj:
            return
        if birth[ri] > birth[rj]:           # make ri the older root
            ri, rj = rj, ri
        if value > birth[rj]:               # zero-length pairs carry no information
            pairs.append((birth[rj], value))
        parent[rj] = ri                      # elder rule: younger component dies

    for idx in order:
        idx = int(idx)
        r, c = divmod(idx, w)
        active[idx] = True
        v = flat[idx]
        for dr, dc in neighbours:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                j = rr * w + cc
                if active[j]:
                    union(idx, j, v)
        if outside and (r == 0 or c == 0 or r == h - 1 or c == w - 1):
            union(idx, n, v)
    return pairs


def persistence_diagrams(f: np.ndarray) -> dict:
    """Persistence diagrams {0: H0 pairs, 1: H1 pairs} of the sublevel filtration of f."""
    f = np.asarray(f, dtype=float)
    assert np.isfinite(f).all(), "image contains NaN or infinite values"
    h0 = _h0_sublevel(f, _N8)
    # H1 = bounded components of {f > t}: run H0 on -f with 4-connectivity + outside
    dual = _h0_sublevel(-f, _N4, outside=True)
    h1 = [(-d, -b) for b, d in dual]        # complement born at -d, filled at -b
    return {0: h0, 1: h1}


def diagram_summary(pairs: list, tau: float = TAU) -> dict:
    """Three numbers that summarise one persistence diagram."""
    life = np.array([d - b for b, d in pairs if np.isfinite(d - b)], dtype=float)
    life = life[life > 0]
    if life.size == 0:
        return {"n_sig": 0.0, "total": 0.0, "entropy": 0.0}
    p = life / life.sum()
    return {"n_sig": float((life > tau).sum()),
            "total": float(life.sum()),
            "entropy": float(-(p * np.log(p)).sum())}


TOPO_CHANNELS = {"a": 1, "L": 0}             # name -> index in the Lab array
TOPO_FEATURE_NAMES = [f"topo_{ch}_h{k}_{s}"
                      for ch in TOPO_CHANNELS for k in (0, 1)
                      for s in ("n_sig", "total", "entropy")]


def topology_features(lab_small: np.ndarray) -> dict:
    """12 topological features from a GRID x GRID CIELAB image."""
    out = {}
    for ch, idx in TOPO_CHANNELS.items():
        dg = persistence_diagrams(lab_small[..., idx])
        for k in (0, 1):
            for s, v in diagram_summary(dg[k]).items():
                out[f"topo_{ch}_h{k}_{s}"] = v
    return out

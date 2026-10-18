"""
image_features.py
-----------------
Step 3 of the image module: turn one photo into a list of numbers
("colour, texture and topological features of the image") that describe it.
The features are chosen in advance from mathematics and clinical knowledge
(they are not learned automatically as in deep learning).

Three groups:
  1. Colour   (CIELAB colour space)
  2. Texture  (GLCM and Shannon entropy)
  3. Topology (persistent homology, see topology.py)

Colour features use the CIELAB colour space:
    L* = lightness (0 = black, 100 = white)
    a* = green (-) <-> red (+)
    b* = blue (-) <-> yellow (+)
    C* = chroma = sqrt(a*^2 + b*^2)  (how colourful; low = whitish/greyish)

Texture features use the GLCM (Gray-Level Co-occurrence Matrix), which
counts how often a pixel of brightness i sits next to a pixel of brightness j.

To reduce the influence of background (skin, beard, gloves, text at the
edges), only the CENTRAL part of the photo is analysed.
"""

import numpy as np
from PIL import Image
from skimage.color import rgb2lab
from skimage.feature import graycomatrix, graycoprops

from topology import topology_features, TOPO_FEATURE_NAMES, GRID

MAX_SIDE = 512          # resize large photos for speed
CENTRE_FRACTION = 0.7   # keep the central 70% of width and height
GLCM_LEVELS = 32        # grey levels used for the GLCM

COLOUR_TEXTURE_NAMES = [
    "mean_L", "std_L",              # lightness and its variation
    "mean_a", "std_a",              # redness and its variation
    "mean_b",                       # yellowness
    "mean_C",                       # colourfulness (chroma)
    "red_fraction",                 # share of clearly red pixels
    "white_fraction",               # share of bright, colourless pixels
    "glcm_contrast", "glcm_homogeneity", "glcm_energy", "glcm_correlation",
    "entropy",                      # disorder of the brightness histogram
]
FEATURE_NAMES = COLOUR_TEXTURE_NAMES + TOPO_FEATURE_NAMES     # 13 + 12 = 25


def load_image(source) -> np.ndarray:
    """Open a photo (file path or uploaded file) as an RGB array, centre-cropped."""
    img = Image.open(source)
    img = img.convert("RGBA").convert("RGB")      # also handles transparent PNGs
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    w, h = img.size
    dw, dh = int(w * (1 - CENTRE_FRACTION) / 2), int(h * (1 - CENTRE_FRACTION) / 2)
    img = img.crop((dw, dh, w - dw, h - dh))
    return np.asarray(img)


def extract_features(source) -> dict:
    """Return the features of one photo as {name: value}."""
    rgb = load_image(source)

    # ---------- colour (CIELAB) ----------
    lab = rgb2lab(rgb / 255.0)
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.sqrt(a ** 2 + b ** 2)

    # ---------- texture (GLCM) ----------
    grey = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2])
    grey_q = (grey / 256 * GLCM_LEVELS).astype(np.uint8)        # 0 .. 31
    glcm = graycomatrix(grey_q, distances=[1, 3],
                        angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
                        levels=GLCM_LEVELS, symmetric=True, normed=True)

    hist = np.bincount(grey_q.ravel(), minlength=GLCM_LEVELS) / grey_q.size
    hist = hist[hist > 0]

    # ---------- topology (persistent homology on a small 64 x 64 copy) ----------
    small = np.asarray(Image.fromarray(rgb).resize((GRID, GRID), Image.LANCZOS))
    topo = topology_features(rgb2lab(small / 255.0))

    return {**topo,
        "mean_L": float(L.mean()),
        "std_L": float(L.std()),
        "mean_a": float(a.mean()),
        "std_a": float(a.std()),
        "mean_b": float(b.mean()),
        "mean_C": float(C.mean()),
        "red_fraction": float((a > 25).mean()),
        "white_fraction": float(((L > 75) & (C < 15)).mean()),
        "glcm_contrast": float(graycoprops(glcm, "contrast").mean()),
        "glcm_homogeneity": float(graycoprops(glcm, "homogeneity").mean()),
        "glcm_energy": float(graycoprops(glcm, "energy").mean()),
        "glcm_correlation": float(graycoprops(glcm, "correlation").mean()),
        "entropy": float(-(hist * np.log2(hist)).sum()),
    }


def feature_vector(features: dict) -> np.ndarray:
    """Features in a fixed order, ready for the model."""
    return np.array([features[name] for name in FEATURE_NAMES])

"""
image_model.py
--------------
Uses the trained photo model (image_model.json) to give a photo a score
between 0 and 1 and a PHOTO LEVEL.

The model is a logistic regression:

    z_i = (x_i - mean_i) / sd_i            (standardised feature)
    s   = beta_0 + sum_i beta_i * z_i
    p   = 1 / (1 + e^(-s))                 (sigmoid)

Photo level from the two thresholds chosen in train_image_model.py:
    p < t_low            -> LOW       (rule-out: sensitivity >= 95% in CV)
    t_low <= p < t_high  -> MODERATE
    p >= t_high          -> HIGH      (rule-in: specificity >= 95% in CV)

The weights are stored in plain JSON, so the calculation is fully visible
and the app does not need scikit-learn.
"""

import json
import math
from pathlib import Path

from image_features import extract_features

MODEL_FILE = Path(__file__).with_name("image_model.json")


def load_model(path: Path = MODEL_FILE) -> dict:
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    # older model files (before 18 Oct) had one threshold only
    if "t_high" not in m:
        # no validated rule-in threshold: the photo can give LOW or MODERATE only
        m["t_low"], m["t_high"], m["old_model"] = m["threshold"], 1.01, True
    return m


def photo_level(p: float, model: dict) -> str:
    if p >= model["t_high"]:
        return "HIGH"
    if p >= model["t_low"]:
        return "MODERATE"
    return "LOW"


def suspicion_score(source, model: dict) -> tuple:
    """Return (probability 0-1, photo level, features dict)."""
    feats = extract_features(source)
    s = model["intercept"]
    for name, mean, scale, beta in zip(model["feature_names"], model["mean"],
                                       model["scale"], model["coef"]):
        s += beta * (feats[name] - mean) / scale
    s = max(-50.0, min(50.0, s))                    # avoid overflow in exp
    p = 1 / (1 + math.exp(-s))
    return p, photo_level(p, model), feats

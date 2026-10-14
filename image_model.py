"""
image_model.py
--------------
Uses the trained image model (saved as image_model.json) to give a photo a
"suspicious appearance" score between 0 and 1.

The model is a logistic regression, the same equation used for the risk score:

    z = beta_0 + sum_i beta_i * x_i        (x_i = standardised feature)
    p = 1 / (1 + e^(-z))                   (sigmoid)

The weights are stored in plain JSON, so the calculation is fully visible
and does not depend on scikit-learn being installed.
"""

import json
import math
from pathlib import Path

from image_features import extract_features, FEATURE_NAMES

MODEL_FILE = Path(__file__).with_name("image_model.json")


def load_model(path: Path = MODEL_FILE) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def suspicion_score(source, model: dict) -> tuple:
    """Return (probability 0-1, is_suspicious True/False, features dict)."""
    feats = extract_features(source)
    z = model["intercept"]
    for name, mean, scale, beta in zip(FEATURE_NAMES, model["mean"],
                                       model["scale"], model["coef"]):
        x = (feats[name] - mean) / scale          # standardise
        z += beta * x
    p = 1 / (1 + math.exp(-z))                    # sigmoid
    return p, p >= model["threshold"], feats

"""
risk_score.py
-------------
Evidence-weighted habit score based on the logistic model

    logit(p) = beta_0 + sum_i beta_i * x_i ,   beta_i = ln(OR_i)

Because the ORs come from case-control studies, beta_0 is unknown, so we
compute only the RELATIVE part:

    S = sum_i beta_i * x_i         (log-odds relative to a non-user)
    combined OR = exp(S)           (how many times higher the odds are)

Design rules (written down so they can be defended in the viva):
 1. Where a study reports a JOINT effect, that single OR is used instead of
    multiplying separate ORs (e.g. male dual users, smoking + alcohol).
    This is how interaction is handled.
 2. Each exposure is counted once (no double counting).
 3. Former users are scored like current users (conservative assumption,
    because the studies did not report separate ORs for quitters).
"""

import math
from dataclasses import dataclass, field
from typing import Optional

from evidence import EVIDENCE
from schema import Patient


@dataclass
class Term:
    key: str          # evidence key
    odds_ratio: float # OR value actually used
    reason: str       # why this term applies


@dataclass
class HabitScore:
    log_score: float                  # S = sum of ln(OR)
    combined_or: float                # exp(S)
    terms: list = field(default_factory=list)
    context_factors: list = field(default_factory=list)  # risk factors without an OR yet
    context_factors_bn: list = field(default_factory=list)  # same, in Bengali for the app


def _or(key: str, override: Optional[dict]) -> float:
    """Use an overridden OR (Monte Carlo) if supplied, otherwise the point estimate."""
    if override and key in override:
        return override[key]
    return EVIDENCE[key].value


def habit_score(p: Patient, or_override: Optional[dict] = None) -> HabitScore:
    terms = []
    smoking_already_counted = False

    # ---- 1. Smokeless tobacco / betel quid ----
    if p.uses_tobacco_slt:
        if p.sex == "female":
            if p.slt_freq_per_day > 5:
                terms.append(Term("slt_women_heavy", _or("slt_women_heavy", or_override),
                                  "Woman using SLT more than 5 times per day"))
            else:
                terms.append(Term("slt_women", _or("slt_women", or_override),
                                  "Woman using smokeless tobacco"))
        else:
            if p.smokes:
                terms.append(Term("dual_use_men", _or("dual_use_men", or_override),
                                  "Man using both smokeless and smoked tobacco (joint OR)"))
                smoking_already_counted = True
            else:
                terms.append(Term("slt_men", _or("slt_men", or_override),
                                  "Man using smokeless tobacco"))
        if p.slt_status == "former":
            terms[-1].reason += " [former use scored as current: conservative]"
    elif p.bq_without_tobacco:
        terms.append(Term("bq_without_tobacco", _or("bq_without_tobacco", or_override),
                          "Betel quid without tobacco"))

    # ---- 2. Smoking and alcohol ----
    smoking_counts = p.smokes and not smoking_already_counted
    if smoking_counts and p.heavy_drinker:
        terms.append(Term("smoking_and_alcohol", _or("smoking_and_alcohol", or_override),
                          "Smoking together with heavy alcohol (joint OR)"))
    elif smoking_counts:
        terms.append(Term("smoking", _or("smoking", or_override), "Smoking"))
    elif p.heavy_drinker:
        terms.append(Term("heavy_alcohol", _or("heavy_alcohol", or_override),
                          "Heavy alcohol, 3 or more drinks per day"))

    # ---- 3. Sum of log-odds ----
    s = sum(math.log(t.odds_ratio) for t in terms)

    # ---- 4. Context factors (used by triage rules, not weighted yet) ----
    # Age, previous cancer and known OPMD are used directly by triage.py, so the
    # Bengali list below shows only the factors that do NOT change the level.
    ctx, ctx_bn = [], []
    if p.age >= 40:              ctx.append("Age 40 or older")
    if p.prev_oral_cancer:       ctx.append("Previous head and neck cancer")
    if p.known_opmd == "yes":    ctx.append("Known oral potentially malignant disorder")
    for flag, en, bn in [
        (p.family_history_hnc, "Family history of head and neck cancer", "পরিবারে মুখ বা গলার ক্যান্সার"),
        (p.immunosuppressed, "Weakened immune system", "রোগ প্রতিরোধ ক্ষমতা কম (HIV, প্রতিস্থাপন, স্টেরয়েড বা কেমো)"),
        (p.outdoor_sun_work, "Outdoor sun exposure (lip)", "বেশিরভাগ সময় রোদে কাজ (ঠোঁটের ঝুঁকি)"),
        (p.chronic_irritation, "Chronic irritation from sharp tooth or denture", "ধারালো দাঁত বা নকল দাঁতের ঘষা"),
        (p.low_fruit_veg, "Low fruit and vegetable intake", "ফল ও শাকসবজি কম খাওয়া"),
    ]:
        if flag:
            ctx.append(en)
            ctx_bn.append(bn)

    return HabitScore(log_score=s, combined_or=math.exp(s), terms=terms,
                      context_factors=ctx, context_factors_bn=ctx_bn)

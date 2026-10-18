"""
risk_score.py
-------------
Evidence-weighted habit score based on the logistic model

    logit(p) = beta_0 + sum_i beta_i * x_i ,   beta_i = ln(OR_i)

Because the ORs come from case-control studies, beta_0 is unknown, so only
the RELATIVE part is computed:

    S = sum_i beta_i * x_i         (log-odds relative to a non-user)
    combined OR = exp(S)           (how many times higher the odds are)

Design rules:
 1. Where a study reports a JOINT effect, that single OR is used instead of
    multiplying separate ORs (male users of both smokeless tobacco and
    cigarettes). This is how interaction is handled.
 2. Each exposure is counted once (no double counting).
 3. Former users are scored like current users (conservative assumption).
"""

import math
from dataclasses import dataclass, field
from typing import Optional

from evidence import EVIDENCE
from schema import Patient


@dataclass
class Term:
    key: str           # evidence key
    odds_ratio: float  # OR value actually used
    reason: str        # why this term applies


@dataclass
class HabitScore:
    log_score: float                   # S = sum of ln(OR)
    combined_or: float                 # exp(S)
    terms: list = field(default_factory=list)


def _or(key: str, override: Optional[dict]) -> float:
    """Use an overridden OR (Monte Carlo) if supplied, otherwise the point estimate."""
    if override and key in override:
        return override[key]
    return EVIDENCE[key].value


def habit_score(p: Patient, or_override: Optional[dict] = None) -> HabitScore:
    terms = []
    smoking_counted = False

    if p.uses_tobacco_slt:
        if p.sex == "female":
            terms.append(Term("slt_women", _or("slt_women", or_override),
                              "Woman using smokeless tobacco"))
        elif p.smokes:
            terms.append(Term("dual_use_men", _or("dual_use_men", or_override),
                              "Man using both smokeless and smoked tobacco (joint OR)"))
            smoking_counted = True
        else:
            terms.append(Term("slt_men", _or("slt_men", or_override),
                              "Man using smokeless tobacco"))
        if p.slt_status == "former":
            terms[-1].reason += " [former use scored as current]"
    elif p.bq_without_tobacco:
        terms.append(Term("bq_without_tobacco", _or("bq_without_tobacco", or_override),
                          "Betel quid without tobacco"))

    if p.smokes and not smoking_counted:
        terms.append(Term("smoking", _or("smoking", or_override), "Smoking"))

    s = sum(math.log(t.odds_ratio) for t in terms)
    return HabitScore(log_score=s, combined_or=math.exp(s), terms=terms)

"""
evidence.py
-----------
Odds ratios (ORs) taken from published studies. Every number used by the
risk model lives here, with its 95% confidence interval and its source,
so the model is fully traceable to the literature.

The weight used in the logistic model is  beta = ln(OR).
"""

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class OddsRatio:
    value: float      # point estimate of the OR
    ci_low: float     # lower bound of the 95% confidence interval
    ci_high: float    # upper bound of the 95% confidence interval
    source: str       # short citation
    note: str = ""    # population / caveats

    @property
    def beta(self) -> float:
        """Log-odds weight: beta = ln(OR)."""
        return math.log(self.value)

    @property
    def se_log(self) -> float:
        """Standard error of ln(OR), recovered from the 95% CI:
        SE = (ln(upper) - ln(lower)) / (2 * 1.96)."""
        return (math.log(self.ci_high) - math.log(self.ci_low)) / (2 * 1.96)

    def sample(self, rng: random.Random) -> float:
        """Draw one plausible OR value (used later for Monte Carlo analysis).
        ln(OR) is assumed to be normally distributed."""
        return math.exp(rng.gauss(self.beta, self.se_log))


# --------------------------------------------------------------------------
# Evidence table (version 1)
# --------------------------------------------------------------------------
EVIDENCE = {
    # Smokeless tobacco (SLT), Bangladesh
    "slt_women": OddsRatio(
        14.33, 6.33, 32.42,
        "Ullah et al. 2025, Tob Use Insights",
        "Any SLT use, women, Dhaka hospital case-control study"),
    "slt_men": OddsRatio(
        5.29, 2.62, 10.67,
        "Ullah et al. 2025, Tob Use Insights",
        "Any SLT use, men, Dhaka hospital case-control study"),
    "slt_women_heavy": OddsRatio(
        32.00, 12.84, 83.02,
        "Ullah et al. 2025, Tob Use Insights",
        "Women using SLT more than 5 times per day (dose-response)"),
    "dual_use_men": OddsRatio(
        17.23, 5.70, 52.01,
        "Ullah et al. 2025, Tob Use Insights",
        "Men using both SLT and smoked tobacco (joint effect)"),
    "bq_without_tobacco": OddsRatio(
        4.43, 1.94, 10.10,
        "Ullah et al. 2025, Tob Use Insights",
        "Betel quid without tobacco, Bangladesh"),

    # Smoking and alcohol (INHANCE consortium, mostly Western populations)
    "smoking": OddsRatio(
        2.37, 1.66, 3.39,
        "Hashibe et al. 2009, CEBP (INHANCE)",
        "Ever tobacco use among never drinkers, head and neck cancer"),
    "heavy_alcohol": OddsRatio(
        2.04, 1.29, 3.21,
        "Hashibe et al. 2007, JNCI (INHANCE)",
        ">=3 drinks/day among never tobacco users, head and neck cancer"),
    "smoking_and_alcohol": OddsRatio(
        5.73, 3.62, 9.06,
        "Hashibe et al. 2009, CEBP (INHANCE)",
        "Joint effect of tobacco and alcohol, head and neck cancer"),
}


def print_evidence_table() -> None:
    """Print the evidence table (useful for the thesis appendix)."""
    print(f"{'Key':22s} {'OR':>6s} {'95% CI':>15s} {'beta':>6s}  Source")
    for key, o in EVIDENCE.items():
        ci = f"({o.ci_low}-{o.ci_high})"
        print(f"{key:22s} {o.value:6.2f} {ci:>15s} {o.beta:6.2f}  {o.source}")


if __name__ == "__main__":
    print_evidence_table()

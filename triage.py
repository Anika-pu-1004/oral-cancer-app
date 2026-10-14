"""
triage.py
---------
Combines (1) red-flag symptoms, (2) the habit score and (3) medical history
into ONE urgency level. The final level is the HIGHEST level triggered by
any rule, so a low habit score can never cancel a red flag.

Levels (low -> high):  LOW < MODERATE < HIGH < URGENT

The thresholds below are design choices of this prototype. They should be
reviewed by a clinician before any real use.
"""

from dataclasses import dataclass, field
from typing import Optional

from schema import Patient
from red_flags import check_red_flags
from risk_score import habit_score, HabitScore

LEVELS = ["LOW", "MODERATE", "HIGH", "URGENT"]

# --- tunable thresholds (combined odds ratio of habits) ---
HABIT_OR_MODERATE = 4.0          # habits alone -> MODERATE
HABIT_OR_MODERATE_AGE40 = 2.0    # habits + age >= 40 -> MODERATE
HABIT_OR_ESCALATE = 4.0          # high-risk habits + early symptom -> HIGH

ADVICE_BN = {
    "URGENT": ("🚨", "জরুরি: ২ সপ্তাহের মধ্যে একজন বিশেষজ্ঞ (ওরাল সার্জন বা নাক-কান-গলা "
                    "বিশেষজ্ঞ) দেখান।"),
    "HIGH": ("⚠️", "৪ সপ্তাহের মধ্যে একজন দন্ত চিকিৎসক বা ওরাল সার্জন দেখান।"),
    "MODERATE": ("🔍", "আগামী ৩ মাসের মধ্যে মুখ পরীক্ষা করান। তামাক ও পান ছাড়ার চেষ্টা করুন।"),
    "LOW": ("✅", "এখন বড় কোনো ঝুঁকির লক্ষণ নেই। নিয়মিত মুখ পরীক্ষা করান। মুখে কোনো ঘা বা দাগ "
                 "২ সপ্তাহের বেশি থাকলে অবশ্যই ডাক্তার দেখান।"),
}

DISCLAIMER_BN = ("এই ফলাফল রোগ নির্ণয় নয়। এটি শুধু বলে দেয় কত দ্রুত ডাক্তার দেখানো উচিত। "
                 "নিশ্চিতভাবে জানার একমাত্র উপায় ডাক্তারের পরীক্ষা ও বায়োপসি।")


@dataclass
class TriageResult:
    level: str
    emoji: str
    advice_bn: str
    reasons_en: list = field(default_factory=list)
    reasons_bn: list = field(default_factory=list)
    score: Optional[HabitScore] = None


def _raise(current: str, new: str) -> str:
    """Return whichever level is higher."""
    return new if LEVELS.index(new) > LEVELS.index(current) else current


def triage(p: Patient, or_override: Optional[dict] = None) -> TriageResult:
    level = "LOW"
    reasons_en, reasons_bn = [], []

    # 1. Symptom rules
    findings = check_red_flags(p)
    for f in findings:
        level = _raise(level, f.level)
        reasons_en.append(f"[{f.level}] {f.reason_en}")
        reasons_bn.append(f.reason_bn)
    has_early_symptom = any(f.level == "MODERATE" for f in findings)

    # 2. Habit score
    hs = habit_score(p, or_override)
    if hs.combined_or >= HABIT_OR_MODERATE:
        level = _raise(level, "MODERATE")
        reasons_en.append(f"[MODERATE] High-risk habits (combined OR = {hs.combined_or:.1f})")
        reasons_bn.append("উচ্চ ঝুঁকির অভ্যাস (তামাক / পান / ধূমপান / মদ্যপান)")
    elif hs.combined_or >= HABIT_OR_MODERATE_AGE40 and p.age >= 40:
        level = _raise(level, "MODERATE")
        reasons_en.append(f"[MODERATE] Risk habits and age 40+ (combined OR = {hs.combined_or:.1f})")
        reasons_bn.append("ঝুঁকিপূর্ণ অভ্যাস এবং বয়স ৪০-এর বেশি")

    # 3. Medical history
    if p.prev_oral_cancer:
        level = _raise(level, "HIGH")
        reasons_en.append("[HIGH] Previous head and neck cancer (risk of second cancer)")
        reasons_bn.append("আগে মুখ বা গলার ক্যান্সার হয়েছিল")
    if p.known_opmd == "yes":
        level = _raise(level, "MODERATE")
        reasons_en.append("[MODERATE] Known oral potentially malignant disorder")
        reasons_bn.append("মুখে ক্যান্সার-পূর্ব রোগ আগে থেকে জানা")

    # 4. Escalation: an early symptom in a high-risk person
    high_risk_person = (hs.combined_or >= HABIT_OR_ESCALATE or p.prev_oral_cancer
                        or p.known_opmd == "yes")
    if has_early_symptom and high_risk_person:
        level = _raise(level, "HIGH")
        reasons_en.append("[HIGH] Early symptom in a high-risk person")
        reasons_bn.append("উচ্চ ঝুঁকির মানুষের মধ্যে নতুন উপসর্গ")

    emoji, advice = ADVICE_BN[level]
    return TriageResult(level, emoji, advice, reasons_en, reasons_bn, hs)


def print_result(name: str, r: TriageResult) -> None:
    print(f"\n=== {name} ===")
    print(f"Level: {r.emoji} {r.level}   |   combined habit OR = {r.score.combined_or:.2f}")
    for t in r.score.terms:
        print(f"   term: {t.key:20s} OR={t.odds_ratio:6.2f}  ({t.reason})")
    for reason in r.reasons_en:
        print(f"   reason: {reason}")
    if r.score.context_factors:
        print(f"   context: {', '.join(r.score.context_factors)}")
    print(f"   advice (BN): {r.advice_bn}")

"""
triage.py
---------
Combines (1) the clinical safety rules, (2) the habit score and (3) medical
history into ONE level from the questions. The final level is the HIGHEST
level triggered by any rule.  Levels (low -> high): LOW < MODERATE < HIGH < URGENT

combine_with_photo() then joins this with the PHOTO LEVEL from the image
model (the main part of the project):
    photo LOW       -> no change
    photo MODERATE  -> at least MODERATE
    photo HIGH      -> at least HIGH, and URGENT if a lesion was also seen
The photo never lowers a level set by the clinical rules.

The thresholds are design choices of this prototype and must be reviewed
by a clinician before any real use.
"""

from dataclasses import dataclass, field
from typing import Optional

from schema import Patient
from red_flags import check_red_flags
from risk_score import habit_score, HabitScore

LEVELS = ["LOW", "MODERATE", "HIGH", "URGENT"]

HABIT_OR_MODERATE = 4.0          # habits alone -> MODERATE
HABIT_OR_MODERATE_AGE40 = 2.0    # habits + age >= 40 -> MODERATE
HABIT_OR_ESCALATE = 4.0          # high-risk habits + new lesion -> HIGH

ADVICE_BN = {
    "URGENT": ("🚨", "২ সপ্তাহের মধ্যে একজন বিশেষজ্ঞ (ওরাল সার্জন বা নাক-কান-গলা "
                    "বিশেষজ্ঞ) দেখান।"),
    "HIGH": ("⚠️", "৪ সপ্তাহের মধ্যে একজন দন্ত চিকিৎসক বা ওরাল সার্জন দেখান।"),
    "MODERATE": ("🔍", "আগামী ৩ মাসের মধ্যে একজন দন্ত চিকিৎসক দিয়ে মুখ পরীক্ষা করান।"),
    "LOW": ("✅", "এখন বড় কোনো ঝুঁকির লক্ষণ নেই। নিয়মিত মুখ পরীক্ষা করান। মুখে কোনো ঘা বা দাগ "
                 "২ সপ্তাহ বা তার বেশি থাকলে অবশ্যই ডাক্তার দেখান।"),
}

QUIT_ADVICE_BN = "🚭 তামাক, জর্দা, পান-সুপারি ও ধূমপান ছাড়লে মুখের ক্যান্সারের ঝুঁকি কমে।"
RECHECK_ADVICE_BN = ("🔁 ঘা বা দাগটি নতুন (২ সপ্তাহের কম)। বেশিরভাগ এমন ঘা বা দাগ নিজে থেকেই "
                     "সেরে যায়। ২ সপ্তাহ পর আবার মুখ দেখুন। তখনো থাকলে দেরি না করে দন্ত "
                     "চিকিৎসক দেখান, অথবা আবার এই অ্যাপে দিন (তখন ফলাফল বেড়ে যাবে)।")
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
    recheck_in_2_weeks: bool = False      # a new (< 2 weeks) lesion
    has_habits: bool = False              # uses tobacco / betel quid / smokes


def _raise(current: str, new: str) -> str:
    """Return whichever level is higher."""
    return new if LEVELS.index(new) > LEVELS.index(current) else current


def triage(p: Patient, or_override: Optional[dict] = None) -> TriageResult:
    level = "LOW"
    reasons_en, reasons_bn = [], []

    findings = check_red_flags(p)
    for f in findings:
        level = _raise(level, f.level)
        reasons_en.append(f"[{f.level}] {f.reason_en}")
        reasons_bn.append(f.reason_bn)
    has_recent_lesion = any(f.recent for f in findings)

    hs = habit_score(p, or_override)
    if hs.combined_or >= HABIT_OR_MODERATE:
        level = _raise(level, "MODERATE")
        reasons_en.append(f"[MODERATE] High-risk habits (combined OR = {hs.combined_or:.1f})")
        reasons_bn.append("উচ্চ ঝুঁকির অভ্যাস (জর্দা / তামাক / পান / ধূমপান)")
    elif hs.combined_or >= HABIT_OR_MODERATE_AGE40 and p.age >= 40:
        level = _raise(level, "MODERATE")
        reasons_en.append(f"[MODERATE] Risk habits and age 40+ (combined OR = {hs.combined_or:.1f})")
        reasons_bn.append("ঝুঁকিপূর্ণ অভ্যাস এবং বয়স ৪০ বা বেশি")

    if p.prev_oral_cancer:
        level = _raise(level, "HIGH")
        reasons_en.append("[HIGH] Previous head and neck cancer (risk of second cancer)")
        reasons_bn.append("আগে মুখ বা গলার ক্যান্সার হয়েছিল")

    if has_recent_lesion and (hs.combined_or >= HABIT_OR_ESCALATE or p.prev_oral_cancer):
        level = _raise(level, "HIGH")
        reasons_en.append("[HIGH] New lesion in a high-risk person")
        reasons_bn.append("উচ্চ ঝুঁকির মানুষের মুখে নতুন ঘা বা দাগ")

    emoji, advice = ADVICE_BN[level]
    return TriageResult(level, emoji, advice, reasons_en, reasons_bn, hs,
                        recheck_in_2_weeks=has_recent_lesion, has_habits=bool(hs.terms))


def combine_with_photo(question_level: str, photo_level: Optional[str], lesion_seen: bool) -> str:
    """Final level from the question level and the photo level (None = no photo)."""
    if photo_level is None or photo_level == "LOW":
        return question_level
    if photo_level == "MODERATE":
        return _raise(question_level, "MODERATE")
    # photo HIGH
    return _raise(question_level, "URGENT" if lesion_seen else "HIGH")


def print_result(name: str, r: TriageResult) -> None:
    print(f"\n=== {name} ===")
    print(f"Level: {r.emoji} {r.level}   |   combined habit OR = {r.score.combined_or:.2f}")
    for t in r.score.terms:
        print(f"   term: {t.key:20s} OR={t.odds_ratio:6.2f}  ({t.reason})")
    for reason in r.reasons_en:
        print(f"   reason: {reason}")
    print(f"   advice (BN): {r.advice_bn}")

"""
schema.py
---------
1. QUESTIONS : the questionnaire (Bengali text for the app), with answer
               types, allowed values and "show only if" conditions.
2. Patient   : one patient's answers as a Python object.
3. validate(): checks that every answer is present and within range.
"""

from dataclasses import dataclass, fields
from typing import Callable, Optional

YES_NO = {True: "হ্যাঁ", False: "না"}
STATUS = {"never": "কখনো না", "former": "আগে করতাম, এখন ছেড়ে দিয়েছি", "current": "এখন করি"}


@dataclass
class Question:
    key: str                     # variable name used in code
    section: str                 # questionnaire section (A-F)
    text_bn: str                 # question shown in the app (Bengali)
    kind: str                    # "int", "float", "bool" or "choice"
    options: Optional[dict] = None          # for "choice"/"bool": value -> Bengali label
    min_value: Optional[float] = None       # for numbers
    max_value: Optional[float] = None
    show_if: Optional[Callable[[dict], bool]] = None  # ask only when this is True


def _uses_slt(a):      return a.get("slt_status") in ("former", "current")
def _uses_chew(a):     return _uses_slt(a) or a.get("bq_without_tobacco") is True
def _smokes(a):        return a.get("smoking_status") in ("former", "current")
def _drinks(a):        return a.get("alcohol_status") in ("former", "current")
def _has_lesion(a):    return any(a.get(k) is True for k in
                                  ("ulcer", "red_patch", "white_patch", "mouth_lump"))

DAYS_HINT = " (১ সপ্তাহ = ৭ দিন, ১ মাস = ৩০ দিন)"


QUESTIONS = [
    # ---------------- A. General ----------------
    Question("age", "A", "আপনার বয়স কত বছর?", "int", min_value=10, max_value=110),
    Question("sex", "A", "আপনি কি পুরুষ না নারী?", "choice",
             {"male": "পুরুষ", "female": "নারী"}),

    # ---------------- B. Smokeless tobacco and betel quid ----------------
    Question("slt_status", "B",
             "আপনি কি জর্দা, সাদাপাতা, গুল, খৈনি বা তামাকপাতা খান?", "choice",
             {"never": "কখনো খাইনি", "former": "আগে খেতাম, এখন ছেড়ে দিয়েছি",
              "current": "এখন খাই"}),
    Question("bq_with_tobacco", "B",
             "পানের সাথে জর্দা বা তামাক খান (বা আগে খেতেন)?", "bool", YES_NO,
             show_if=_uses_slt),
    Question("other_slt", "B",
             "পান ছাড়া আলাদাভাবে গুল, সাদাপাতা, খৈনি বা তামাকপাতা ব্যবহার করেন (বা করতেন)?",
             "bool", YES_NO, show_if=_uses_slt),
    # Asked only of people who never used jorda/tobacco: for tobacco users the
    # tobacco risk already dominates, and the question would only confuse them.
    Question("bq_without_tobacco", "B",
             "আপনি কি পান-সুপারি খান (বা আগে খেতেন)?", "bool", YES_NO,
             show_if=lambda a: a.get("slt_status") == "never"),
    Question("slt_freq_per_day", "B",
             "দিনে কতবার পান, জর্দা বা তামাক খান (বা খেতেন)?", "int",
             min_value=0, max_value=100, show_if=_uses_chew),
    Question("slt_years", "B",
             "কত বছর ধরে খাচ্ছেন (বা খেয়েছেন)?", "float",
             min_value=0, max_value=90, show_if=_uses_chew),

    # ---------------- C. Smoking ----------------
    Question("smoking_status", "C",
             "আপনি কি ধূমপান করেন (সিগারেট, বিড়ি বা হুক্কা)?", "choice", STATUS),
    Question("cig_per_day", "C",
             "দিনে কয়টি সিগারেট বা বিড়ি খান (বা খেতেন)?", "int",
             min_value=0, max_value=100, show_if=_smokes),
    Question("smoking_years", "C",
             "কত বছর ধরে ধূমপান করছেন (বা করেছেন)?", "float",
             min_value=0, max_value=90, show_if=_smokes),

    # ---------------- D. Alcohol ----------------
    Question("alcohol_status", "D", "আপনি কি মদ্যপান করেন?", "choice", STATUS),
    Question("drinks_per_day", "D",
             "গড়ে দিনে কত পেগ মদ খান (বা খেতেন)? (১ পেগ, ১ ক্যান বিয়ার বা "
             "১ গ্লাস তাড়ি = ১ ধরুন; ১ ছোট গ্লাস চোলাই = ২ ধরুন)", "float",
             min_value=0, max_value=50, show_if=_drinks),

    # ---------------- E. Medical history ----------------
    Question("prev_oral_cancer", "E",
             "আগে কখনো মুখ, গলা বা মাথা-ঘাড়ের ক্যান্সার হয়েছিল?", "bool", YES_NO),
    Question("known_opmd", "E",
             "কোনো ডাক্তার কি কখনো বলেছেন যে মুখে এমন দাগ বা রোগ আছে যা পরে ক্যান্সার হতে "
             "পারে (যেমন সাদা দাগ, বা মুখের ভেতরের চামড়া শক্ত হয়ে যাওয়া)?", "choice",
             {"yes": "হ্যাঁ", "no": "না", "unknown": "জানি না"}),
    Question("family_history_hnc", "E",
             "পরিবারে (বাবা-মা, ভাই-বোন) কারো মুখ বা গলার ক্যান্সার হয়েছে?", "bool", YES_NO),
    Question("immunosuppressed", "E",
             "আপনার কি HIV আছে, কিডনি বা অন্য অঙ্গ প্রতিস্থাপন হয়েছে, অথবা দীর্ঘদিন "
             "স্টেরয়েড বা ক্যান্সারের (কেমো) ওষুধ খাচ্ছেন?",
             "bool", YES_NO),
    Question("outdoor_sun_work", "E",
             "দিনের বেশিরভাগ সময় কি রোদে কাজ করেন (যেমন কৃষিকাজ, রিকশা চালানো)?",
             "bool", YES_NO),
    Question("chronic_irritation", "E",
             "কোনো ভাঙা বা ধারালো দাঁত, বা ঢিলা নকল দাঁত কি মুখের ভেতরে ঘষা লাগে?",
             "bool", YES_NO),
    Question("low_fruit_veg", "E", "আপনি কি খুব কম ফল ও শাকসবজি খান?", "bool", YES_NO),

    # ---------------- F. Symptoms ----------------
    Question("ulcer", "F", "মুখে বা ঠোঁটে কি কোনো ঘা আছে?", "bool", YES_NO),
    Question("ulcer_days", "F", "ঘা-টি কত দিন ধরে আছে?" + DAYS_HINT, "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("ulcer") is True),
    Question("red_patch", "F",
             "মুখের ভেতরে কি একটা নির্দিষ্ট লাল বা লাল-সাদা মেশানো দাগ আছে, যা আশেপাশ থেকে "
             "আলাদা দেখায়? (পুরো মুখের স্বাভাবিক লালচে ভাব, জিভের ছোট লাল বিন্দু বা "
             "কামড় লাগার দাগ ধরবেন না)", "bool", YES_NO),
    Question("red_patch_days", "F", "লাল বা লাল-সাদা দাগটি কত দিন ধরে আছে?" + DAYS_HINT, "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("red_patch") is True),
    Question("white_patch", "F",
             "মুখের ভেতরে কি সাদা দাগ আছে যা ঘষলেও ওঠে না?", "bool", YES_NO),
    Question("white_patch_days", "F", "সাদা দাগটি কত দিন ধরে আছে?" + DAYS_HINT, "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("white_patch") is True),
    Question("mouth_lump", "F",
             "মুখের ভেতরে বা ঠোঁটে কি কোনো চাকা, গুটি বা ফোলা আছে? (তালুর ঠিক মাঝখানে, "
             "অথবা নিচের মাড়ির ভেতরের দিকে জিভের পাশে দুই দিকে একই রকম, বহু বছর ধরে না বদলানো "
             "মসৃণ হাড়ের মতো উঁচু অংশ স্বাভাবিক, এটি ধরবেন না। সন্দেহ হলে 'হ্যাঁ' দিন)", "bool", YES_NO),
    Question("mouth_lump_days", "F", "চাকা বা ফোলাটি কত দিন ধরে আছে?" + DAYS_HINT, "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("mouth_lump") is True),
    Question("induration", "F",
             "ঘা, দাগ বা চাকার জায়গায় আঙুল দিয়ে হালকা চাপলে কি শক্ত লাগে?", "bool", YES_NO,
             show_if=_has_lesion),
    Question("unexplained_bleeding", "F",
             "ঘা, দাগ বা চাকা থেকে কি কোনো কারণ ছাড়াই রক্ত পড়ে? (কামড় লাগা, আঘাত বা "
             "দাঁত মাজার সময় মাড়ি থেকে রক্ত পড়া ধরবেন না)", "bool", YES_NO,
             show_if=_has_lesion),
    # Recorded for research only (not used in the rules); asked only when a lesion exists.
    Question("lesion_site", "F", "ঘা, দাগ বা চাকাটি মুখের কোন জায়গায়?", "choice",
             {"buccal": "গালের ভেতরে", "tongue_lateral": "জিভের পাশে",
              "floor_of_mouth": "জিভের নিচে / মুখের তলায়", "gum": "মাড়িতে",
              "lip": "ঠোঁটে", "palate": "তালুতে", "other": "অন্য জায়গায় / একাধিক জায়গায়"},
             show_if=_has_lesion),
    Question("neck_lump", "F", "গলায় কি কোনো চাকা বা গুটি আছে?", "bool", YES_NO),
    Question("neck_lump_days", "F", "গলার চাকাটি কত দিন ধরে আছে?" + DAYS_HINT, "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("neck_lump") is True),
    Question("numbness", "F", "জিভ, ঠোঁট বা মুখে কি অবশ ভাব লাগে?", "bool", YES_NO),
    Question("numbness_days", "F", "অবশ ভাবটি কত দিন ধরে আছে?" + DAYS_HINT, "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("numbness") is True),
    Question("loose_tooth", "F",
             "আঘাত বা অনেক দিনের মাড়ির রোগ ছাড়া কি হঠাৎ দাঁত নড়ে গেছে?", "bool", YES_NO),
    Question("dysphagia", "F", "দাঁতের সমস্যা (দাঁত না থাকা বা দাঁত ব্যথা) ছাড়াই কি খাবার চিবাতে বা গিলতে কষ্ট হয়?", "bool", YES_NO),
    Question("dysphagia_days", "F", "গিলতে বা চিবাতে কষ্ট কত দিন ধরে হচ্ছে?" + DAYS_HINT, "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("dysphagia") is True),
    Question("spicy_burning", "F",
             "আগে যে ঝাল সহজে খেতে পারতেন, এখন অল্প ঝালেও কি মুখের ভেতর জ্বালা করে?", "bool", YES_NO),
    Question("reduced_mouth_opening", "F",
             "রোগীকে সবচেয়ে বড় করে হা করতে বলুন। তার নিজের তিনটি আঙুল (তর্জনী, মধ্যমা, "
             "অনামিকা) একসাথে খাড়াভাবে মুখে ঢোকে কি?", "bool",
             {True: "ঢোকে না (মুখ কম খোলে)", False: "ঢোকে"}),
    Question("ear_pain", "F", "কানে কোনো সমস্যা ছাড়াই কি কান ব্যথা করে?", "bool", YES_NO),
    Question("weight_loss", "F", "চেষ্টা না করেও কি ওজন কমে যাচ্ছে?", "bool", YES_NO),
    Question("mouth_pain", "F", "দাঁত ব্যথা ছাড়া, মুখের ভেতরে কোনো এক জায়গায় কি একটানা ব্যথা আছে?", "bool", YES_NO),
    Question("mouth_pain_days", "F", "ব্যথাটি কত দিন ধরে আছে?" + DAYS_HINT, "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("mouth_pain") is True),
]

QUESTION_BY_KEY = {q.key: q for q in QUESTIONS}


@dataclass
class Patient:
    # A. General
    age: int = 0
    sex: str = "male"
    # B. Smokeless tobacco / betel quid
    slt_status: str = "never"
    bq_with_tobacco: bool = False
    other_slt: bool = False
    bq_without_tobacco: bool = False
    slt_freq_per_day: int = 0
    slt_years: float = 0
    # C. Smoking
    smoking_status: str = "never"
    cig_per_day: int = 0
    smoking_years: float = 0
    # D. Alcohol
    alcohol_status: str = "never"
    drinks_per_day: float = 0
    # E. Medical history
    prev_oral_cancer: bool = False
    known_opmd: str = "no"
    family_history_hnc: bool = False
    immunosuppressed: bool = False
    outdoor_sun_work: bool = False
    chronic_irritation: bool = False
    low_fruit_veg: bool = False
    # F. Symptoms
    ulcer: bool = False
    ulcer_days: int = 0
    red_patch: bool = False
    red_patch_days: int = 0
    white_patch: bool = False
    white_patch_days: int = 0
    mouth_lump: bool = False
    mouth_lump_days: int = 0
    induration: bool = False
    neck_lump: bool = False
    neck_lump_days: int = 0
    unexplained_bleeding: bool = False
    numbness: bool = False
    numbness_days: int = 0
    loose_tooth: bool = False
    dysphagia: bool = False
    dysphagia_days: int = 0
    spicy_burning: bool = False
    reduced_mouth_opening: bool = False
    ear_pain: bool = False
    weight_loss: bool = False
    mouth_pain: bool = False
    mouth_pain_days: int = 0
    lesion_site: str = "none"

    # ---------- derived variables (computed, never asked) ----------
    @property
    def uses_tobacco_slt(self) -> bool:
        return self.slt_status in ("former", "current")

    @property
    def smokes(self) -> bool:
        return self.smoking_status in ("former", "current")

    @property
    def heavy_drinker(self) -> bool:
        return self.alcohol_status in ("former", "current") and self.drinks_per_day >= 3

    @property
    def pack_years(self) -> float:
        """(cigarettes per day / 20) x years smoked."""
        return (self.cig_per_day / 20) * self.smoking_years if self.smokes else 0.0

    @property
    def slt_exposure(self) -> float:
        """Times per day x years: an SLT analogue of pack-years."""
        return self.slt_freq_per_day * self.slt_years

    @property
    def dual_user(self) -> bool:
        return self.uses_tobacco_slt and self.smokes


def shown_answers(answers: dict) -> dict:
    """Keep only answers to questions that are actually shown, checking the
    questions in order exactly like the app does (a leftover answer to a hidden
    question can therefore never change a later question or the result)."""
    kept = {}
    for q in QUESTIONS:
        if q.show_if is not None and not q.show_if(kept):
            continue
        if q.key in answers:
            kept[q.key] = answers[q.key]
    return kept


def validate(answers: dict) -> list:
    """Return a list of error messages (empty list = all answers valid)."""
    errors = []
    kept = shown_answers(answers)
    for q in QUESTIONS:
        if q.show_if is not None and not q.show_if(kept):
            continue                          # question was not asked
        if q.key not in answers or answers[q.key] is None:
            errors.append(f"Missing answer: {q.key}")
            continue
        v = answers[q.key]
        if q.kind in ("int", "float"):
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                errors.append(f"{q.key}: must be a number")
            elif not (q.min_value <= v <= q.max_value):
                errors.append(f"{q.key}: {v} is outside {q.min_value}-{q.max_value}")
        elif q.kind == "bool" and not isinstance(v, bool):
            errors.append(f"{q.key}: must be True or False")
        elif q.kind == "choice" and v not in q.options:
            errors.append(f"{q.key}: '{v}' is not one of {list(q.options)}")
    return errors


def patient_from_answers(answers: dict) -> Patient:
    """Validate the answers and build a Patient (unasked fields keep defaults).

    Answers to questions that were NOT shown (their show_if is False) are
    ignored, so a leftover answer can never change the result."""
    errors = validate(answers)
    if errors:
        raise ValueError("Invalid answers:\n  " + "\n  ".join(errors))
    names = {f.name for f in fields(Patient)}
    return Patient(**{k: v for k, v in shown_answers(answers).items() if k in names})

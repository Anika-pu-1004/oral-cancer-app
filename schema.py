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
             "পান ছাড়া আলাদাভাবে গুল, সাদাপাতা বা খৈনি ব্যবহার করেন (বা করতেন)?",
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
             "সাধারণত দিনে কত গ্লাস বা পেগ পান করেন (বা করতেন)?", "float",
             min_value=0, max_value=50, show_if=_drinks),

    # ---------------- E. Medical history ----------------
    Question("prev_oral_cancer", "E",
             "আগে কখনো মুখ, গলা বা মাথা-ঘাড়ের ক্যান্সার হয়েছিল?", "bool", YES_NO),
    Question("known_opmd", "E",
             "কোনো ডাক্তার কি কখনো বলেছেন যে আপনার মুখে ক্যান্সার-পূর্ব দাগ বা রোগ আছে "
             "(যেমন লিউকোপ্লাকিয়া, বা মুখের ভেতর শক্ত হয়ে যাওয়া/OSMF)?", "choice",
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
    Question("ulcer", "F", "মুখে বা ঠোঁটে কি এমন কোনো ঘা আছে যা শুকাচ্ছে না?", "bool", YES_NO),
    Question("ulcer_days", "F", "ঘা-টি কত দিন ধরে আছে?", "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("ulcer") is True),
    Question("red_patch", "F",
             "মুখের ভেতরে কি লাল দাগ, বা লাল-সাদা মেশানো দাগ আছে?", "bool", YES_NO),
    Question("white_patch", "F",
             "মুখের ভেতরে কি সাদা দাগ আছে যা ঘষলেও ওঠে না?", "bool", YES_NO),
    Question("white_patch_days", "F", "সাদা দাগটি কত দিন ধরে আছে?", "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("white_patch") is True),
    Question("mouth_lump", "F",
             "মুখের ভেতরে বা ঠোঁটে কি কোনো চাকা, গুটি বা ফোলা আছে?", "bool", YES_NO),
    Question("neck_lump", "F", "গলায় কি কোনো চাকা বা গুটি আছে?", "bool", YES_NO),
    Question("neck_lump_days", "F", "গলার চাকাটি কত দিন ধরে আছে?", "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("neck_lump") is True),
    Question("unexplained_bleeding", "F",
             "কোনো কারণ ছাড়াই কি মুখ থেকে রক্ত পড়ে?", "bool", YES_NO),
    Question("numbness", "F", "জিভ, ঠোঁট বা মুখে কি অবশ ভাব লাগে?", "bool", YES_NO),
    Question("loose_tooth", "F", "কোনো কারণ ছাড়া কি হঠাৎ দাঁত নড়ে গেছে?", "bool", YES_NO),
    Question("dysphagia", "F", "খাবার গিলতে বা চিবাতে কি কষ্ট হয়?", "bool", YES_NO),
    Question("reduced_mouth_opening", "F",
             "মুখ কি আগের মতো পুরো খুলতে পারেন না?", "bool", YES_NO),
    Question("ear_pain", "F", "কানে কোনো সমস্যা ছাড়াই কি কান ব্যথা করে?", "bool", YES_NO),
    Question("weight_loss", "F", "চেষ্টা না করেও কি ওজন কমে যাচ্ছে?", "bool", YES_NO),
    Question("mouth_pain", "F", "মুখের ভেতরে আক্রান্ত অংশে কি একটানা ব্যথা আছে?", "bool", YES_NO),
    Question("mouth_pain_days", "F", "ব্যথাটি কত দিন ধরে আছে?", "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("mouth_pain") is True),
    Question("lesion_site", "F", "সমস্যাটি মুখের কোন জায়গায়?", "choice",
             {"buccal": "গালের ভেতরে", "tongue_lateral": "জিভের পাশে",
              "floor_of_mouth": "জিভের নিচে / মুখের তলায়", "gum": "মাড়িতে",
              "lip": "ঠোঁটে", "palate": "তালুতে", "none": "কোনো সমস্যা নেই / নির্দিষ্ট নয়"}),
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
    white_patch: bool = False
    white_patch_days: int = 0
    mouth_lump: bool = False
    neck_lump: bool = False
    neck_lump_days: int = 0
    unexplained_bleeding: bool = False
    numbness: bool = False
    loose_tooth: bool = False
    dysphagia: bool = False
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


def validate(answers: dict) -> list:
    """Return a list of error messages (empty list = all answers valid)."""
    errors = []
    for q in QUESTIONS:
        if q.show_if is not None and not q.show_if(answers):
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
    """Validate the answers and build a Patient (unasked fields keep defaults)."""
    errors = validate(answers)
    if errors:
        raise ValueError("Invalid answers:\n  " + "\n  ".join(errors))
    names = {f.name for f in fields(Patient)}
    return Patient(**{k: v for k, v in answers.items() if k in names})

"""
schema.py
---------
1. QUESTIONS : the SHORT clinical questionnaire (Bengali text for the app).
               Version of 18 Oct 2026: only the questions a doctor needs
               and that a photo cannot answer (how long a lesion has been
               there, whether it is hard, bleeding, neck lump, habits).
2. Patient   : one patient's answers as a Python object.
3. validate(): checks that every answer is present and within range.
"""

from dataclasses import dataclass, fields
from typing import Callable, Optional

YES_NO = {True: "হ্যাঁ", False: "না"}
STATUS = {"never": "কখনো করেননি", "former": "আগে করতেন, এখন ছেড়ে দিয়েছেন", "current": "এখন করেন"}
DAYS_HINT = " (১ সপ্তাহ = ৭ দিন, ১ মাস = ৩০ দিন)"


@dataclass
class Question:
    key: str                     # variable name used in code
    section: str                 # questionnaire section
    text_bn: str                 # question shown in the app (Bengali)
    kind: str                    # "int", "bool" or "choice"
    options: Optional[dict] = None          # value -> Bengali label
    min_value: Optional[float] = None       # for numbers
    max_value: Optional[float] = None
    show_if: Optional[Callable[[dict], bool]] = None  # ask only when this is True


def _has_lesion(a):    return a.get("lesion") is True


QUESTIONS = [
    # ---------------- A. Person and habits ----------------
    Question("age", "A", "রোগীর বয়স কত বছর?", "int", min_value=10, max_value=110),
    Question("sex", "A", "রোগী পুরুষ না নারী?", "choice", {"male": "পুরুষ", "female": "নারী"}),
    Question("slt_status", "A",
             "জর্দা, গুল, সাদাপাতা, খৈনি বা তামাকপাতা খান?", "choice",
             {"never": "কখনো খাননি", "former": "আগে খেতেন, এখন ছেড়ে দিয়েছেন",
              "current": "এখন খান"}),
    # tobacco users are already scored for tobacco, so the question is not needed for them
    Question("bq_without_tobacco", "A", "পান-সুপারি খান (বা আগে খেতেন)?", "bool", YES_NO,
             show_if=lambda a: a.get("slt_status") == "never"),
    Question("smoking_status", "A", "ধূমপান করেন (সিগারেট, বিড়ি বা হুক্কা)?", "choice", STATUS),
    Question("prev_oral_cancer", "A",
             "আগে কখনো মুখ, গলা বা মাথা-ঘাড়ের ক্যান্সার হয়েছিল?", "bool", YES_NO),

    # ---------------- B. What the health worker sees and feels ----------------
    Question("lesion", "B",
             "মুখের ভেতরে বা ঠোঁটে কি কোনো ঘা, আশেপাশ থেকে আলাদা লাল বা সাদা দাগ, "
             "বা চাকা আছে? (পুরো মুখের স্বাভাবিক লালচে ভাব, কামড়ের দাগ, আর বহু বছর ধরে "
             "একই রকম থাকা মসৃণ হাড়ের মতো উঁচু অংশ ধরবেন না। সন্দেহ হলে 'হ্যাঁ' দিন)",
             "bool", YES_NO),
    Question("lesion_days", "B", "ঘা, দাগ বা চাকাটি কত দিন ধরে আছে?" + DAYS_HINT, "int",
             min_value=0, max_value=3650, show_if=_has_lesion),
    Question("induration", "B",
             "ঘা, দাগ বা চাকার জায়গায় আঙুল দিয়ে হালকা চাপলে কি শক্ত লাগে?", "bool", YES_NO,
             show_if=_has_lesion),
    Question("unexplained_bleeding", "B",
             "ঘা, দাগ বা চাকা থেকে কি কোনো কারণ ছাড়াই রক্ত পড়ে? (কামড়, আঘাত বা দাঁত "
             "মাজার সময় মাড়ি থেকে রক্ত পড়া ধরবেন না)", "bool", YES_NO, show_if=_has_lesion),
    Question("neck_lump", "B", "গলার পাশে বা চোয়ালের নিচে (ঘাড়ে) কি কোনো চাকা বা গুটি আছে?",
             "bool", YES_NO),
    Question("neck_lump_days", "B", "ঘাড়ের চাকাটি কত দিন ধরে আছে?" + DAYS_HINT, "int",
             min_value=0, max_value=3650, show_if=lambda a: a.get("neck_lump") is True),
    Question("reduced_mouth_opening", "B",
             "রোগীকে সবচেয়ে বড় করে হাঁ করতে বলুন। তার নিজের তিনটি আঙুল (তর্জনী, মধ্যমা, "
             "অনামিকা) একসাথে খাড়াভাবে মুখে ঢোকে কি?", "bool",
             {True: "ঢোকে না (মুখ কম খোলে)", False: "ঢোকে"}),
]

QUESTION_BY_KEY = {q.key: q for q in QUESTIONS}


@dataclass
class Patient:
    age: int = 0
    sex: str = "male"
    slt_status: str = "never"
    bq_without_tobacco: bool = False
    smoking_status: str = "never"
    prev_oral_cancer: bool = False
    lesion: bool = False
    lesion_days: int = 0
    induration: bool = False
    unexplained_bleeding: bool = False
    neck_lump: bool = False
    neck_lump_days: int = 0
    reduced_mouth_opening: bool = False

    # ---------- derived variables (computed, never asked) ----------
    @property
    def uses_tobacco_slt(self) -> bool:
        return self.slt_status in ("former", "current")

    @property
    def smokes(self) -> bool:
        return self.smoking_status in ("former", "current")


def shown_answers(answers: dict) -> dict:
    """Keep only answers to questions that are actually shown, checking the
    questions in order exactly like the app does (a leftover answer to a hidden
    question can therefore never change the result)."""
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
        if q.key not in kept or kept[q.key] is None:
            errors.append(f"Missing answer: {q.key}")
            continue
        v = kept[q.key]
        if q.kind == "int":
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
    return Patient(**{k: v for k, v in shown_answers(answers).items() if k in names})

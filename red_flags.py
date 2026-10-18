"""
red_flags.py
------------
Clinical safety rules for the things a photo cannot show: how long a lesion
has been there, whether it is hard or bleeding, a neck lump, and mouth opening.
Habits and the photo can only RAISE the level set here, never lower it.

Rules (clinical "RULE": a single lesion persisting 3 weeks or more is
suspicious; NICE NG12 suspected cancer guideline; Oral Cancer Foundation):
    ulcer / red or white patch / lump in mouth or lip:
        less than 14 days -> MODERATE (re-check after 2 weeks)
        14 to 21 days     -> HIGH
        more than 21 days -> URGENT
    lesion that feels hard (induration)            -> URGENT
    lesion that bleeds without a cause             -> URGENT
    neck lump: up to 21 days -> HIGH, more than 21 -> URGENT
    three fingers do not fit (possible OSMF)       -> HIGH
"""

from dataclasses import dataclass
from schema import Patient


@dataclass
class Finding:
    level: str            # "URGENT", "HIGH" or "MODERATE"
    reason_en: str        # for the report
    reason_bn: str        # shown in the app
    recent: bool = False  # a lesion under 14 days whose level rises if it persists


def check_red_flags(p: Patient) -> list:
    f = []

    def add(level, en, bn, recent=False):
        f.append(Finding(level, en, bn, recent))

    if p.lesion:
        if p.lesion_days > 21:
            add("URGENT", "Lesion (ulcer, patch or lump) for more than 3 weeks (NICE NG12, RULE)",
                "৩ সপ্তাহের বেশি সময় ধরে ঘা, দাগ বা চাকা")
        elif p.lesion_days >= 14:
            add("HIGH", "Lesion for 2-3 weeks", "২–৩ সপ্তাহ ধরে ঘা, দাগ বা চাকা")
        else:
            add("MODERATE", "Recent lesion, less than 2 weeks (re-check after 2 weeks)",
                "নতুন ঘা, দাগ বা চাকা (২ সপ্তাহের কম)", recent=True)
        if p.induration:
            add("URGENT", "Lesion feels hard on palpation (induration)",
                "ঘা, দাগ বা চাকার জায়গা চাপ দিলে শক্ত লাগে")
        if p.unexplained_bleeding:
            add("URGENT", "Unexplained bleeding from the lesion (OCF)",
                "কারণ ছাড়াই ঘা, দাগ বা চাকা থেকে রক্ত পড়া")

    if p.neck_lump:
        if p.neck_lump_days > 21:
            add("URGENT", "Persistent neck lump for more than 3 weeks (NICE NG12)",
                "৩ সপ্তাহের বেশি সময় ধরে ঘাড়ে চাকা")
        else:
            add("HIGH", "Recent neck lump (urgent if it persists past 3 weeks)",
                "ঘাড়ে নতুন চাকা (৩ সপ্তাহের বেশি থাকলে জরুরি)")

    if p.reduced_mouth_opening:
        add("HIGH", "Reduced mouth opening, three fingers do not fit (possible oral submucous fibrosis)",
            "মুখে তিন আঙুল ঢোকে না (মুখের ভেতরের আবরণ শক্ত হওয়ার রোগ, ওরাল সাবমিউকাস ফাইব্রোসিসের লক্ষণ হতে পারে)")
    return f

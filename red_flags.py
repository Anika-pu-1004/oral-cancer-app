"""
red_flags.py
------------
Symptom rules. These are checked BEFORE the risk score and can never be
lowered by it: a person with a red-flag sign is always URGENT, whatever
their habits.

Sources: NICE NG12 suspected cancer referral guideline (UK); Oral Cancer
Foundation / CDC background paper (2-4 week rule); Mayo Clinic symptom list.
"""

from dataclasses import dataclass
from schema import Patient


@dataclass
class Finding:
    level: str        # "URGENT" or "HIGH" or "MODERATE"
    reason_en: str    # for the report
    reason_bn: str    # shown in the app


def check_red_flags(p: Patient) -> list:
    f = []

    # ---------- URGENT: specialist within 2 weeks ----------
    if p.ulcer and p.ulcer_days > 21:
        f.append(Finding("URGENT", "Non-healing ulcer for more than 3 weeks (NICE NG12)",
                         "৩ সপ্তাহের বেশি সময় ধরে না-শুকানো ঘা"))
    if p.red_patch:
        f.append(Finding("URGENT", "Red or red-and-white patch (NICE NG12)",
                         "মুখে লাল বা লাল-সাদা মেশানো দাগ"))
    if p.mouth_lump:
        f.append(Finding("URGENT", "Lump in the mouth or on the lip (NICE NG12)",
                         "মুখে বা ঠোঁটে চাকা বা ফোলা"))
    if p.neck_lump and p.neck_lump_days > 21:
        f.append(Finding("URGENT", "Persistent neck lump for more than 3 weeks (NICE NG12)",
                         "৩ সপ্তাহের বেশি সময় ধরে গলায় চাকা"))
    if p.unexplained_bleeding:
        f.append(Finding("URGENT", "Unexplained oral bleeding (OCF)",
                         "কারণ ছাড়া মুখ থেকে রক্ত পড়া"))
    if p.numbness:
        f.append(Finding("URGENT", "Numbness of tongue, lip or mouth (OCF)",
                         "জিভ, ঠোঁট বা মুখে অবশ ভাব"))
    if p.loose_tooth:
        f.append(Finding("URGENT", "Sudden tooth mobility without cause (OCF)",
                         "কারণ ছাড়া হঠাৎ দাঁত নড়া"))
    if p.dysphagia:
        f.append(Finding("URGENT", "Difficulty swallowing or chewing (OCF, Mayo)",
                         "গিলতে বা চিবাতে কষ্ট"))

    # ---------- HIGH: dentist / oral surgeon within 4 weeks ----------
    if p.ulcer and 14 <= p.ulcer_days <= 21:
        f.append(Finding("HIGH", "Ulcer for 2-3 weeks (OCF 2-4 week rule)",
                         "২–৩ সপ্তাহ ধরে ঘা"))
    if p.white_patch and p.white_patch_days >= 14:
        f.append(Finding("HIGH", "White patch for 2 weeks or more (possible leukoplakia)",
                         "২ সপ্তাহ বা তার বেশি সময় ধরে সাদা দাগ"))
    if p.neck_lump and p.neck_lump_days <= 21:
        f.append(Finding("HIGH", "Recent neck lump (re-check; urgent if it persists past 3 weeks)",
                         "গলায় নতুন চাকা (৩ সপ্তাহের বেশি থাকলে জরুরি)"))
    if p.mouth_pain and p.mouth_pain_days >= 14:
        f.append(Finding("HIGH", "Persistent mouth pain for 2 weeks or more",
                         "২ সপ্তাহ বা তার বেশি সময় ধরে মুখে ব্যথা"))
    if p.reduced_mouth_opening:
        f.append(Finding("HIGH", "Reduced mouth opening (possible oral submucous fibrosis)",
                         "মুখ পুরো খুলতে না পারা (সাবমিউকাস ফাইব্রোসিসের লক্ষণ হতে পারে)"))

    # ---------- MODERATE: early or non-specific symptoms ----------
    if p.ulcer and p.ulcer_days < 14:
        f.append(Finding("MODERATE", "Recent ulcer (see a dentist if not healed within 2 weeks)",
                         "নতুন ঘা (২ সপ্তাহে না শুকালে ডাক্তার দেখান)"))
    if p.white_patch and p.white_patch_days < 14:
        f.append(Finding("MODERATE", "Recent white patch",
                         "নতুন সাদা দাগ"))
    if p.mouth_pain and p.mouth_pain_days < 14:
        f.append(Finding("MODERATE", "Recent mouth pain", "নতুন মুখের ব্যথা"))
    if p.ear_pain:
        f.append(Finding("MODERATE", "Ear pain without ear disease (possible referred pain)",
                         "কানের সমস্যা ছাড়া কান ব্যথা"))
    if p.weight_loss:
        f.append(Finding("MODERATE", "Unintentional weight loss", "অনিচ্ছাকৃত ওজন কমা"))

    return f

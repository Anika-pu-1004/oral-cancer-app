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
    """Symptom rules. Duration thresholds follow the clinical 'RULE' (a single lesion
    persisting 3 weeks or more is suspicious) so that short-lived, harmless findings
    reported by lay observers do not trigger an urgent referral."""
    f = []

    def add(level, en, bn):
        f.append(Finding(level, en, bn))

    # ---------- ulcer ----------
    if p.ulcer:
        if p.ulcer_days > 21:
            add("URGENT", "Non-healing ulcer for more than 3 weeks (NICE NG12)",
                "৩ সপ্তাহের বেশি সময় ধরে না-শুকানো ঘা")
        elif p.ulcer_days >= 14:
            add("HIGH", "Ulcer for 2-3 weeks (OCF 2-4 week rule)", "২–৩ সপ্তাহ ধরে ঘা")
        else:
            add("MODERATE", "Recent ulcer (see a dentist if not healed within 2 weeks)",
                "নতুন ঘা (২ সপ্তাহে না শুকালে ডাক্তার দেখান)")

    # ---------- distinct red or red-and-white patch ----------
    if p.red_patch:
        if p.red_patch_days > 21:
            add("URGENT", "Distinct red or red-and-white patch for more than 3 weeks (NICE NG12, RULE)",
                "৩ সপ্তাহের বেশি সময় ধরে লাল বা লাল-সাদা দাগ")
        elif p.red_patch_days >= 14:
            add("HIGH", "Distinct red or red-and-white patch for 2-3 weeks",
                "২–৩ সপ্তাহ ধরে লাল বা লাল-সাদা দাগ")
        else:
            add("MODERATE", "Recent red patch (re-check if not gone within 2 weeks)",
                "নতুন লাল দাগ (২ সপ্তাহে না সারলে ডাক্তার দেখান)")

    # ---------- white patch ----------
    if p.white_patch:
        if p.white_patch_days >= 14:
            add("HIGH", "White patch for 2 weeks or more (possible leukoplakia)",
                "২ সপ্তাহ বা তার বেশি সময় ধরে সাদা দাগ")
        else:
            add("MODERATE", "Recent white patch", "নতুন সাদা দাগ")

    # ---------- lump in mouth or lip ----------
    if p.mouth_lump:
        if p.mouth_lump_days > 21:
            add("URGENT", "Lump in the mouth or lip for more than 3 weeks (NICE NG12)",
                "৩ সপ্তাহের বেশি সময় ধরে মুখে বা ঠোঁটে চাকা")
        else:
            add("HIGH", "Recent lump in the mouth or lip (urgent if it persists past 3 weeks)",
                "মুখে বা ঠোঁটে নতুন চাকা (৩ সপ্তাহের বেশি থাকলে জরুরি)")

    # ---------- induration: firm on palpation ----------
    if p.induration and (p.ulcer or p.red_patch or p.white_patch or p.mouth_lump):
        add("URGENT", "Lesion feels hard on palpation (induration)",
            "ঘা, দাগ বা চাকার জায়গা চাপ দিলে শক্ত লাগে")

    # ---------- neck lump ----------
    if p.neck_lump:
        if p.neck_lump_days > 21:
            add("URGENT", "Persistent neck lump for more than 3 weeks (NICE NG12)",
                "৩ সপ্তাহের বেশি সময় ধরে গলায় চাকা")
        else:
            add("HIGH", "Recent neck lump (re-check; urgent if it persists past 3 weeks)",
                "গলায় নতুন চাকা (৩ সপ্তাহের বেশি থাকলে জরুরি)")

    # ---------- bleeding from a lesion ----------
    if p.unexplained_bleeding:
        add("URGENT", "Bleeding from an oral lesion (OCF)", "মুখের ঘা বা দাগ থেকে রক্ত পড়া")

    # ---------- numbness ----------
    if p.numbness:
        if p.numbness_days > 21:
            add("URGENT", "Numbness of tongue, lip or mouth for more than 3 weeks (OCF)",
                "৩ সপ্তাহের বেশি সময় ধরে অবশ ভাব")
        else:
            add("MODERATE", "Recent numbness", "নতুন অবশ ভাব")

    # ---------- loose tooth (without trauma or long-standing gum disease) ----------
    if p.loose_tooth:
        add("HIGH", "Sudden tooth mobility without trauma or gum disease",
            "আঘাত বা মাড়ির রোগ ছাড়া হঠাৎ দাঁত নড়া")

    # ---------- difficulty swallowing ----------
    if p.dysphagia:
        if p.dysphagia_days > 21:
            add("URGENT", "Difficulty swallowing or chewing for more than 3 weeks",
                "৩ সপ্তাহের বেশি সময় ধরে গিলতে বা চিবাতে কষ্ট")
        else:
            add("MODERATE", "Recent difficulty swallowing or chewing",
                "নতুন করে গিলতে বা চিবাতে কষ্ট")

    # ---------- pain ----------
    if p.mouth_pain:
        if p.mouth_pain_days >= 14:
            add("HIGH", "Persistent pain in the affected area for 2 weeks or more",
                "২ সপ্তাহ বা তার বেশি সময় ধরে আক্রান্ত জায়গায় ব্যথা")
        else:
            add("MODERATE", "Recent mouth pain", "নতুন মুখের ব্যথা")

    # ---------- oral submucous fibrosis signs ----------
    if p.reduced_mouth_opening:
        add("HIGH", "Reduced mouth opening (possible oral submucous fibrosis)",
            "মুখ পুরো খুলতে না পারা (সাবমিউকাস ফাইব্রোসিসের লক্ষণ হতে পারে)")
    if p.spicy_burning:
        add("MODERATE", "Burning sensation with spicy food (early sign of oral submucous fibrosis)",
            "ঝাল খেলে মুখ জ্বালা (সাবমিউকাস ফাইব্রোসিসের প্রথম লক্ষণ হতে পারে)")

    # ---------- other ----------
    if p.ear_pain:
        add("MODERATE", "Ear pain without ear disease (possible referred pain)",
            "কানের সমস্যা ছাড়া কান ব্যথা")
    if p.weight_loss:
        add("MODERATE", "Unintentional weight loss", "অনিচ্ছাকৃত ওজন কমা")

    return f

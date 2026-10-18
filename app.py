"""
app.py
------
Bengali web app for community health workers (version of 18 Oct 2026).

MAIN PART: the mouth photo
  photo -> 25 features (colour, texture, topology / persistent homology)
        -> logistic regression -> probability p -> PHOTO LEVEL
           p < t_low -> LOW,  t_low <= p < t_high -> MODERATE,  p >= t_high -> HIGH
SAFETY PART: a short clinical questionnaire (what a photo cannot show:
  how long, hard or bleeding, neck lump, mouth opening, habits)
FINAL LEVEL: triage.combine_with_photo(); the photo never lowers a level set
by the clinical rules.  Levels: 🚨 URGENT  ⚠️ HIGH  🔍 MODERATE  ✅ LOW

Run with:  streamlit run app.py
"""

import streamlit as st

from schema import QUESTIONS, patient_from_answers, _has_lesion
from triage import (triage, combine_with_photo, LEVELS, ADVICE_BN, DISCLAIMER_BN,
                    QUIT_ADVICE_BN, RECHECK_ADVICE_BN)
from image_model import load_model, suspicion_score, MODEL_FILE

SECTION_TITLES = {"A": "খ. রোগী ও অভ্যাস", "B": "গ. মুখ পরীক্ষা (স্বাস্থ্যকর্মী নিজে দেখবেন)"}
LEVEL_BN = {"URGENT": "জরুরি", "HIGH": "উচ্চ ঝুঁকি", "MODERATE": "মাঝারি ঝুঁকি", "LOW": "কম ঝুঁকি"}
LEVEL_TIME = {"URGENT": "২ সপ্তাহের মধ্যে বিশেষজ্ঞ", "HIGH": "৪ সপ্তাহের মধ্যে ডাক্তার",
              "MODERATE": "৩ মাসের মধ্যে পরীক্ষা", "LOW": "নিয়মিত পরীক্ষা"}
# red - yellow - blue - green, far apart on the colour wheel; each level also has its own symbol
LEVEL_COLOUR = {"URGENT": "#A32D2D", "HIGH": "#FAC775", "MODERATE": "#B5D4F4", "LOW": "#C0DD97"}
LEVEL_TEXT = {"URGENT": "#FCEBEB", "HIGH": "#412402", "MODERATE": "#042C53", "LOW": "#173404"}
LEVEL_EDGE = {"URGENT": "#791F1F", "HIGH": "#BA7517", "MODERATE": "#378ADD", "LOW": "#639922"}
LEVEL_STEP = {"URGENT": "৪", "HIGH": "৩", "MODERATE": "২", "LOW": "১"}
PHOTO_LEVEL_BN = {"LOW": "✅ কম সন্দেহ", "MODERATE": "🔍 মাঝামাঝি", "HIGH": "⚠️ বেশি সন্দেহ"}

st.set_page_config(page_title="মুখের ক্যান্সার ঝুঁকি নির্ণয়", page_icon="🦷", layout="centered")


@st.cache_resource
def get_image_model():
    """Load the trained image model once (None if the file is missing)."""
    return load_model() if MODEL_FILE.exists() else None


def ladder_html(level: str) -> str:
    """4-step ladder, most serious at the top; the patient's step is highlighted."""
    rows = []
    for lvl in ["URGENT", "HIGH", "MODERATE", "LOW"]:
        here = lvl == level
        bg = LEVEL_COLOUR[lvl] if here else "rgba(128,128,128,0.08)"
        fg = LEVEL_TEXT[lvl] if here else "inherit"
        weight = 700 if here else 400
        marker = "◀ এই রোগী" if here else ""
        rows.append(
            f'<div style="display:flex; justify-content:space-between; align-items:center;'
            f' background:{bg}; color:{fg}; font-weight:{weight}; padding:8px 14px;'
            f' margin:4px 0; border-radius:6px; border-left:8px solid {LEVEL_EDGE[lvl]};">'
            f'<span>স্তর {LEVEL_STEP[lvl]}: {ADVICE_BN[lvl][0]} {LEVEL_BN[lvl]} '
            f'<small>({LEVEL_TIME[lvl]})</small></span><span>{marker}</span></div>')
    return ('<div style="font-size:0.95rem;"><div style="opacity:0.7;">▲ সবচেয়ে গুরুতর</div>'
            + "".join(rows) + '<div style="opacity:0.7;">▼ সবচেয়ে কম গুরুতর</div></div>')


def result_box_html(level: str) -> str:
    emoji, advice = ADVICE_BN[level]
    return (f'<div style="background:{LEVEL_COLOUR[level]}; color:{LEVEL_TEXT[level]};'
            f' border:2px solid {LEVEL_EDGE[level]}; padding:20px 22px; border-radius:10px;">'
            f'<div style="font-size:1.9rem; font-weight:800;">'
            f'{emoji} {LEVEL_BN[level]}: {LEVEL_TIME[level]}</div>'
            f'<div style="font-size:1.1rem; margin-top:8px;">{advice}</div></div>')


# ---------------------------------------------------------------- header
st.title("🦷 মুখের ক্যান্সার ঝুঁকি নির্ণয়")
st.caption("স্বাস্থ্যকর্মীদের জন্য: মুখের ছবি ও কয়েকটি জরুরি প্রশ্ন থেকে রোগীকে কত দ্রুত "
           "বিশেষজ্ঞ দেখাতে হবে, তা নির্ধারণে সহায়তা")
st.info(DISCLAIMER_BN)
st.info("👩‍⚕️ এই অ্যাপ ব্যবহার করবেন প্রশিক্ষিত স্বাস্থ্যকর্মী। ছবি আপনিই তুলবেন, আর রোগীর মুখ "
        "টর্চ দিয়ে দেখে ও আঙুল দিয়ে হালকা চাপ দিয়ে প্রশ্নের উত্তর দেবেন।")
st.warning("⚠️ এটি একটি গবেষণার নমুনা (research prototype), বাস্তব চিকিৎসায় ব্যবহারের জন্য নয়। "
           "আসল রোগীর ছবি আপলোড করবেন না।")

with st.sidebar:
    st.header("এই অ্যাপ সম্পর্কে")
    st.write("মুখের ছবি (মূল অংশ) ও কয়েকটি জরুরি প্রশ্ন থেকে ঝুঁকির স্তর জানায় "
             "(উপরেরটা সবচেয়ে গুরুতর):")
    for lvl in ["URGENT", "HIGH", "MODERATE", "LOW"]:
        st.write(f"{ADVICE_BN[lvl][0]} **{LEVEL_BN[lvl]}**: {LEVEL_TIME[lvl]}")
    st.caption("গবেষণা প্রকল্প: Premier University, Chattogram")
    if st.button("🔄 নতুন রোগী"):
        st.session_state.clear()
        st.rerun()

# ---------------------------------------------------------------- photo (main part)
st.subheader("ক. মুখের ছবি (মূল অংশ)")
with st.expander("📸 ছবি তোলার নিয়ম"):
    st.markdown(
        "- ছবি তোলার আগে রোগী পানি দিয়ে ভালো করে **কুলি করবেন** (পানের রস দূর করতে)\n"
        "- মোবাইলের **পেছনের ক্যামেরা** আর টর্চ বা ফ্ল্যাশ ব্যবহার করুন\n"
        "- ঘা বা দাগটি **ছবির ঠিক মাঝখানে** রাখুন, ১০–১৫ সেমি দূর থেকে তুলুন\n"
        "- দরকার হলে চামচ দিয়ে গাল সরিয়ে ধরুন; শুধু মুখের ভেতরের অংশ যেন দেখা যায়\n"
        "- ছবি ঝাপসা হলে আবার তুলুন"
    )
photo = st.file_uploader("ছবি আপলোড করুন", type=["jpg", "jpeg", "png", "webp"])
if photo is not None:
    try:
        st.image(photo, caption="আপলোড করা ছবি", width=300)
    except Exception:
        st.error("ছবিটি খোলা যাচ্ছে না। অন্য একটি ছবি দিন।")

# ---------------------------------------------------------------- short questionnaire
answers = {}
current_section = None
for q in QUESTIONS:
    if q.section != current_section:
        current_section = q.section
        st.subheader(SECTION_TITLES[q.section])
    if q.show_if is not None and not q.show_if(answers):
        continue                                  # follow-up question not needed
    if q.kind == "bool":
        answers[q.key] = st.radio(q.text_bn, [True, False], index=None, key=q.key,
                                  format_func=lambda v, o=q.options: o[v], horizontal=True)
    elif q.kind == "choice":
        answers[q.key] = st.radio(q.text_bn, list(q.options), index=None, key=q.key,
                                  format_func=lambda v, o=q.options: o[v])
    else:  # int
        answers[q.key] = st.number_input(q.text_bn, min_value=int(q.min_value),
                                         max_value=int(q.max_value), value=None,
                                         step=1, key=q.key)

# ---------------------------------------------------------------- result
st.divider()
if st.button("✅ ফলাফল দেখুন", type="primary", use_container_width=True):

    # 1. every question that was shown must be answered
    missing = [q.text_bn for q in QUESTIONS if q.key in answers and answers[q.key] is None]
    if missing:
        st.error("নিচের প্রশ্নগুলোর উত্তর দেওয়া হয়নি:")
        for text in missing:
            st.write(f"• {text}")
        st.stop()

    # 2. photo -> probability -> photo level
    model = get_image_model()
    photo_state, prob, plevel = "none", None, None
    if photo is not None and model is None:
        photo_state = "no_model"
    elif photo is not None:
        photo.seek(0)
        try:
            from PIL import Image
            w, h = Image.open(photo).size
            photo.seek(0)
            if min(w, h) < 200:
                raise ValueError("photo too small")
            prob, plevel, feats = suspicion_score(photo, model)
            if not (0.0 <= prob <= 1.0):
                raise ValueError("invalid score")
        except Exception:
            photo_state, plevel = "bad_photo", None
        else:
            if feats["mean_L"] < 15 or feats["mean_L"] > 92:
                photo_state, plevel = "bad_light", None
            else:
                photo_state = "ok"

    # 3. questions -> clinical level, then the final level
    patient = patient_from_answers(answers)
    result = triage(patient)
    question_level = result.level
    lesion_seen = _has_lesion(answers)
    level = combine_with_photo(question_level, plevel, lesion_seen)

    if photo_state == "ok" and plevel != "LOW" and not lesion_seen:
        st.warning("🟡 **মুখ আবার দেখুন:** ছবিতে অস্বাভাবিক কিছু থাকতে পারে, কিন্তু প্রশ্নে "
                   "কোনো ঘা, দাগ বা চাকার কথা বলা হয়নি। টর্চ দিয়ে রোগীর মুখ ও ঠোঁট আবার ভালো "
                   "করে দেখুন। ঘা, দাগ বা চাকা থাকলে উত্তর ঠিক করে আবার **ফলাফল দেখুন** চাপুন।")

    st.markdown(result_box_html(level), unsafe_allow_html=True)
    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.markdown(ladder_html(level), unsafe_allow_html=True)

    # 4. how the result was reached
    st.markdown("### ফলাফল কীভাবে এলো")
    st.markdown("**ধাপ ১: ছবির বিশ্লেষণ (মূল অংশ):**")
    if photo_state == "none":
        st.write("• কোনো ছবি দেওয়া হয়নি। ফলাফল শুধু প্রশ্নের উত্তর থেকে এসেছে; "
                 "ভালো ফলাফলের জন্য ছবি দিন।")
    elif photo_state == "no_model":
        st.write("• ⚠️ ছবির মডেল (image_model.json) পাওয়া যায়নি, তাই ছবি বিশ্লেষণ করা হয়নি")
    elif photo_state == "bad_photo":
        st.write("• ⚠️ ছবিটি খোলা যায়নি বা খুব ছোট (কমপক্ষে ২০০ পিক্সেল লাগবে)। আবার তুলুন।")
    elif photo_state == "bad_light":
        st.write("• ⚠️ ছবিটি খুব অন্ধকার বা খুব উজ্জ্বল, তাই বিশ্লেষণে ধরা হয়নি। "
                 "ভালো আলোতে আবার তুলুন।")
    else:
        st.progress(min(max(prob, 0.0), 1.0), text=f"ছবির সম্ভাবনা (p): {prob:.0%}")
        high_txt = (f", {model['t_high']:.0%} বা বেশি হলে বেশি সন্দেহ"
                    if model["t_high"] <= 1 else "")
        st.write(f"• সীমা: {model['t_low']:.0%}-এর কম হলে কম সন্দেহ{high_txt}। "
                 f"এই ছবি: **{PHOTO_LEVEL_BN[plevel]}**")
        if model.get("old_model"):
            st.caption("⚠️ পুরোনো ছবির মডেল: নতুন train_image_model.py চালিয়ে মডেল আবার "
                       "তৈরি না করা পর্যন্ত ছবি সর্বোচ্চ 'মাঝামাঝি' দেখাবে।")
        st.caption("ছবির মডেলটি ইন্টারনেটের অল্প কিছু ছবি দিয়ে শেখানো, তাই ভুল হতে পারে। "
                   "চূড়ান্ত সিদ্ধান্ত ডাক্তারের।")

    st.markdown(f"**ধাপ ২: প্রশ্নের উত্তর অনুযায়ী:** {ADVICE_BN[question_level][0]} "
                f"{LEVEL_BN[question_level]}")
    if result.reasons_bn:
        for r in result.reasons_bn:
            st.write(f"• {r}")
    elif result.has_habits:
        st.write("• কোনো ঘা, দাগ বা চাকা পাওয়া যায়নি। ঝুঁকির অভ্যাস আছে, তবে বয়স ও অভ্যাস "
                 "মিলিয়ে ঝুঁকি এখনো মাঝারি স্তরে পৌঁছায়নি")
    else:
        st.write("• প্রশ্নের উত্তরে কোনো ঝুঁকির লক্ষণ বা অভ্যাস পাওয়া যায়নি")

    st.markdown("**ধাপ ৩: চূড়ান্ত ফলাফল:**")
    if level != question_level:
        extra = " (ছবিতে বেশি সন্দেহ এবং মুখে ঘা বা দাগও আছে)" if level == "URGENT" else ""
        st.write(f"• {ADVICE_BN[question_level][0]} {LEVEL_BN[question_level]} থেকে "
                 f"**{ADVICE_BN[level][0]} {LEVEL_BN[level]}**: ছবির কারণে স্তর বেড়েছে{extra}")
    else:
        note = " (ছবি কখনো স্তর কমায় না)" if photo_state == "ok" else ""
        st.write(f"• {ADVICE_BN[level][0]} **{LEVEL_BN[level]}**{note}")

    if result.recheck_in_2_weeks and level == "MODERATE" and plevel in (None, "LOW"):
        st.info(RECHECK_ADVICE_BN)
    if result.has_habits:
        st.info(QUIT_ADVICE_BN)

    with st.expander("🔍 বিস্তারিত (স্বাস্থ্যকর্মী ও গবেষকের জন্য)"):
        st.write(f"অভ্যাসের সম্মিলিত Odds Ratio: **{result.score.combined_or:.2f}**")
        for t in result.score.terms:
            st.write(f"- {t.key}: OR = {t.odds_ratio:.2f} ({t.reason})")
        if model is not None:
            st.write(f"ছবির মডেল: {model.get('feature_set', '')}; "
                     f"AUC = {model['cv_auc']:.2f}; t_low = {model['t_low']:.2f}, "
                     f"t_high = {model['t_high']:.2f}; ছবি = {model['n_images']}টি")
        if photo_state == "ok":
            topo = {k: round(v, 2) for k, v in feats.items() if k.startswith("topo_")}
            st.write("টপোলজির সংখ্যা (persistent homology):", topo)

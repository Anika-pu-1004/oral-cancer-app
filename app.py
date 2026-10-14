"""
app.py
------
Bengali web app for community health workers.

  1. Questionnaire (sections A-F)      -> triage.py  (red flags + risk score)
  2. Optional mouth photo               -> image_model.py (suspicion score)
  3. Final urgency level: 🔴 🟠 🟡 🟢

Safety rule: the photo can only RAISE the urgency level, never lower it.

The result is shown in three steps so the health worker can see WHY:
  step 1 = level from the questionnaire, step 2 = photo analysis,
  step 3 = final level (and whether the photo raised it),
plus a 4-step ladder showing where this level sits (URGENT at the top).

Run with:  streamlit run app.py
"""

import streamlit as st

from schema import QUESTIONS, patient_from_answers
from triage import triage, LEVELS, ADVICE_BN, DISCLAIMER_BN
from image_model import load_model, suspicion_score, MODEL_FILE

# ---------------------------------------------------------------- settings
SECTION_TITLES = {
    "A": "ক. সাধারণ তথ্য",
    "B": "খ. পান, জর্দা ও তামাক",
    "C": "গ. ধূমপান",
    "D": "ঘ. মদ্যপান",
    "E": "ঙ. চিকিৎসার ইতিহাস",
    "F": "চ. উপসর্গ",
}
LEVEL_BN = {"URGENT": "জরুরি", "HIGH": "উচ্চ ঝুঁকি", "MODERATE": "মাঝারি ঝুঁকি", "LOW": "কম ঝুঁকি"}
LEVEL_TIME = {"URGENT": "২ সপ্তাহের মধ্যে বিশেষজ্ঞ", "HIGH": "৪ সপ্তাহের মধ্যে ডাক্তার",
              "MODERATE": "৩ মাসের মধ্যে পরীক্ষা", "LOW": "নিয়মিত পরীক্ষা"}
LEVEL_COLOUR = {"URGENT": "#c62828", "HIGH": "#ef6c00", "MODERATE": "#f9a825", "LOW": "#2e7d32"}
LEVEL_TINT = {"URGENT": "#c62828", "HIGH": "#fff3e0", "MODERATE": "#fffde7", "LOW": "#e8f5e9"}
LEVEL_STEP = {"URGENT": "৪", "HIGH": "৩", "MODERATE": "২", "LOW": "১"}
IMAGE_RAISES_TO = "HIGH"          # a suspicious photo raises the level to at least HIGH

st.set_page_config(page_title="মুখের ক্যান্সার ঝুঁকি নির্ণয়", page_icon="🦷", layout="centered")


@st.cache_resource
def get_image_model():
    """Load the trained image model once (None if the file is missing)."""
    return load_model() if MODEL_FILE.exists() else None


def combine(question_level: str, photo_suspicious: bool) -> str:
    """Final level: the photo can raise the level to HIGH, never lower it."""
    if photo_suspicious and LEVELS.index(IMAGE_RAISES_TO) > LEVELS.index(question_level):
        return IMAGE_RAISES_TO
    return question_level


def ladder_html(level: str) -> str:
    """4-step ladder, most serious at the top; the patient's step is highlighted."""
    rows = []
    for lvl in ["URGENT", "HIGH", "MODERATE", "LOW"]:
        here = lvl == level
        bg = LEVEL_COLOUR[lvl] if here else "rgba(128,128,128,0.08)"
        fg = "white" if here else "inherit"
        weight = 700 if here else 400
        marker = "◀ এই রোগী" if here else ""
        rows.append(
            f'<div style="display:flex; justify-content:space-between; align-items:center;'
            f' background:{bg}; color:{fg}; font-weight:{weight}; padding:8px 14px;'
            f' margin:4px 0; border-radius:6px; border-left:8px solid {LEVEL_COLOUR[lvl]};">'
            f'<span>ধাপ {LEVEL_STEP[lvl]}: {ADVICE_BN[lvl][0]} {LEVEL_BN[lvl]} '
            f'<small>({LEVEL_TIME[lvl]})</small></span><span>{marker}</span></div>')
    return ('<div style="font-size:0.95rem;"><div style="opacity:0.7;">▲ সবচেয়ে গুরুতর</div>'
            + "".join(rows) + '<div style="opacity:0.7;">▼ সবচেয়ে কম গুরুতর</div></div>')


def result_box_html(level: str) -> str:
    emoji, advice = ADVICE_BN[level]
    if level == "URGENT":   # solid red with white text: impossible to miss
        return (f'<div style="background:{LEVEL_COLOUR[level]}; color:white; padding:20px 22px;'
                f' border-radius:10px;"><div style="font-size:1.9rem; font-weight:800;">'
                f'⚠️ {LEVEL_BN[level]}: {LEVEL_TIME[level]}</div>'
                f'<div style="font-size:1.1rem; margin-top:8px;">{advice}</div></div>')
    return (f'<div style="background:{LEVEL_TINT[level]}; border-left:10px solid {LEVEL_COLOUR[level]};'
            f' padding:18px 22px; border-radius:10px; color:#1a1a1a;">'
            f'<div style="font-size:1.7rem; font-weight:800; color:{LEVEL_COLOUR[level]};">'
            f'{emoji} {LEVEL_BN[level]}: {LEVEL_TIME[level]}</div>'
            f'<div style="font-size:1.1rem; margin-top:8px;">{advice}</div></div>')


# ---------------------------------------------------------------- header
st.title("🦷 মুখের ক্যান্সার ঝুঁকি নির্ণয়")
st.caption("স্বাস্থ্যকর্মীদের জন্য: রোগীকে কত দ্রুত বিশেষজ্ঞ দেখাতে হবে, তা নির্ধারণে সহায়তা")
st.info(DISCLAIMER_BN)
st.warning("⚠️ এটি একটি গবেষণার নমুনা (research prototype), বাস্তব চিকিৎসায় ব্যবহারের জন্য নয়। আসল রোগীর ছবি আপলোড করবেন না।")

with st.sidebar:
    st.header("এই অ্যাপ সম্পর্কে")
    st.write("প্রশ্নের উত্তর ও মুখের ছবি দেখে ঝুঁকির স্তর জানায় (উপরেরটা সবচেয়ে গুরুতর):")
    for lvl in ["URGENT", "HIGH", "MODERATE", "LOW"]:
        st.write(f"{ADVICE_BN[lvl][0]} **{LEVEL_BN[lvl]}**: {LEVEL_TIME[lvl]}")
    st.caption("গবেষণা প্রকল্প: Premier University, Chattogram")
    if st.button("🔄 নতুন রোগী"):
        st.session_state.clear()
        st.rerun()

# ---------------------------------------------------------------- questionnaire
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
    elif q.kind == "int":
        answers[q.key] = st.number_input(q.text_bn, min_value=int(q.min_value),
                                         max_value=int(q.max_value), value=None,
                                         step=1, key=q.key)
    else:  # float
        answers[q.key] = st.number_input(q.text_bn, min_value=float(q.min_value),
                                         max_value=float(q.max_value), value=None,
                                         step=1.0, key=q.key)

# ---------------------------------------------------------------- photo
st.subheader("ছ. মুখের ছবি (ঐচ্ছিক)")
with st.expander("📸 ছবি তোলার নিয়ম"):
    st.markdown(
        "- ছবি তোলার আগে রোগী পানি দিয়ে ভালো করে **কুলি করবেন** (পানের রস দূর করতে)\n"
        "- পর্যাপ্ত **আলোতে** ছবি তুলুন\n"
        "- ক্ষত বা দাগটি **ছবির ঠিক মাঝখানে** রাখুন\n"
        "- কাছ থেকে তুলুন, যাতে শুধু মুখের ভেতরের অংশ দেখা যায়"
    )
photo = st.file_uploader("ছবি আপলোড করুন", type=["jpg", "jpeg", "png", "webp"])
if photo is not None:
    st.image(photo, caption="আপলোড করা ছবি", width=300)

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

    # 2. questionnaire -> triage
    patient = patient_from_answers(answers)
    result = triage(patient)
    question_level = result.level
    reasons_bn = list(result.reasons_bn)

    # 3. photo
    model = get_image_model()
    photo_state, prob, suspicious = "none", None, False
    if photo is not None and model is None:
        photo_state = "no_model"
    elif photo is not None:
        photo.seek(0)
        prob, suspicious, feats = suspicion_score(photo, model)
        if feats["mean_L"] < 15 or feats["mean_L"] > 92:
            photo_state, suspicious = "bad_light", False
        else:
            photo_state = "suspicious" if suspicious else "clear"
    if suspicious:
        reasons_bn.append("ছবিতে সম্ভাব্য সন্দেহজনক চিহ্ন")

    level = combine(question_level, suspicious)

    # 4. final result + ladder
    st.markdown(result_box_html(level), unsafe_allow_html=True)
    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.markdown(ladder_html(level), unsafe_allow_html=True)

    # 5. how the result was reached (three steps)
    st.markdown("### ফলাফল কীভাবে এলো")
    st.markdown(f"**ধাপ ১: প্রশ্নের উত্তর অনুযায়ী:** {ADVICE_BN[question_level][0]} "
                f"{LEVEL_BN[question_level]}")
    if result.reasons_bn:
        for r in result.reasons_bn:
            st.write(f"• {r}")
    else:
        st.write("• কোনো ঝুঁকির উপসর্গ বা অভ্যাস পাওয়া যায়নি")

    st.markdown("**ধাপ ২: ছবির বিশ্লেষণ:**")
    if photo_state == "none":
        st.write("• কোনো ছবি দেওয়া হয়নি")
    elif photo_state == "no_model":
        st.write("• ⚠️ ছবির মডেল (image_model.json) পাওয়া যায়নি, তাই ছবি বিশ্লেষণ করা হয়নি")
    elif photo_state == "bad_light":
        st.write("• ⚠️ ছবিটি খুব অন্ধকার বা খুব উজ্জ্বল, তাই বিশ্লেষণে ধরা হয়নি। "
                 "ভালো আলোতে আবার তুলুন।")
    else:
        st.progress(min(max(prob, 0.0), 1.0),
                    text=f"সন্দেহের স্কোর: {prob:.0%}  (সীমা: {model['threshold']:.0%})")
        if photo_state == "suspicious":
            st.write("• 📷 ছবিতে **সম্ভাব্য** সন্দেহজনক চিহ্ন দেখা গেছে। একজন ডাক্তারের দেখা দরকার।")
        else:
            st.write("• 📷 ছবিতে স্পষ্ট সন্দেহজনক চিহ্ন পাওয়া যায়নি। তবে এটি নিশ্চয়তা নয়; "
                     "উপসর্গ থাকলে ডাক্তার দেখান।")
        st.caption("ছবির বিশ্লেষণ শুধু সহায়ক। এটি কখনো কখনো স্বাভাবিক লাল জিভকেও "
                   "সন্দেহজনক বলতে পারে। চূড়ান্ত সিদ্ধান্ত ডাক্তারের।")

    st.markdown("**ধাপ ৩: চূড়ান্ত ফলাফল:**")
    if level != question_level:
        st.write(f"• {ADVICE_BN[question_level][0]} {LEVEL_BN[question_level]} থেকে "
                 f"**{ADVICE_BN[level][0]} {LEVEL_BN[level]}**: ছবির কারণে স্তর বেড়েছে")
    elif photo_state in ("suspicious", "clear"):
        st.write(f"• {ADVICE_BN[level][0]} **{LEVEL_BN[level]}**: ছবি স্তর বদলায়নি "
                 "(ছবি কখনো স্তর কমায় না, আর সর্বোচ্চ উচ্চ ঝুঁকি পর্যন্ত বাড়াতে পারে)")
    else:
        st.write(f"• {ADVICE_BN[level][0]} **{LEVEL_BN[level]}**")

    with st.expander("🔍 বিস্তারিত (স্বাস্থ্যকর্মী ও গবেষকের জন্য)"):
        st.write(f"অভ্যাসের সম্মিলিত Odds Ratio: **{result.score.combined_or:.2f}**")
        for t in result.score.terms:
            st.write(f"- {t.key}: OR = {t.odds_ratio:.2f} ({t.reason})")
        if result.score.context_factors:
            st.write("অন্যান্য ঝুঁকি: " + ", ".join(result.score.context_factors))
        if model is not None:
            st.write(f"ছবির মডেল: AUC = {model['cv_auc']:.2f}, "
                     f"sensitivity = {model['cv_sensitivity']:.2f}, "
                     f"specificity = {model['cv_specificity']:.2f}, "
                     f"threshold = {model['threshold']:.2f}")

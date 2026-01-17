# pages/2_سياق_الجذر.py
# -*- coding: utf-8 -*-

import re
import pandas as pd
import streamlit as st

# =======================
# إعدادات ثابتة (مخفية عن المستخدم)
# =======================
CSV_PATH = "quran_corrected_global.csv"
CL1_PATH = "Cl1.xlsx"

# أعمدة CSV
COL_TASH = "3"        # الآية بالتشكيل
COL_PLAIN = "4"       # الآية بدون تشكيل
COL_SURAH_NO = "1"    # رقم السورة
COL_AYAH_NO = "2"     # رقم الآية
COL_SURAH_T = "10"    # اسم السورة بالتشكيل
COL_SURAH_P = "11"    # اسم السورة بدون تشكيل

# أعمدة Cl1.xlsx
CL1_WORD_COL = "الكلمة"
CL1_ROOT_COL = "الجذر"

# =======================
# أدوات لغوية
# =======================
ARABIC_DIACRITICS_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
TOKEN_RE = re.compile(r"[^\s]+")

def normalize_arabic(text: str) -> str:
    if not isinstance(text, str):
        return ""
    t = ARABIC_DIACRITICS_RE.sub("", text)
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ٱ", "ا")
    t = t.replace("ة", "ه")
    t = t.replace("ى", "ي")
    t = t.replace("ؤ", "و").replace("ئ", "ي")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def tokenize(text: str):
    if not isinstance(text, str) or not text:
        return []
    return TOKEN_RE.findall(text)

def safe_int(x):
    try:
        return int(str(x))
    except Exception:
        return 10**9

# =======================
# تحميل البيانات
# =======================
@st.cache_data(show_spinner=False)
def load_quran_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype=str, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path, dtype=str, encoding="utf-8-sig")

@st.cache_data(show_spinner=False)
def load_xlsx(path: str) -> pd.DataFrame:
    return pd.read_excel(path, dtype=str)

@st.cache_data(show_spinner=False)
def build_root_maps(lex_df: pd.DataFrame):
    exact_map = {}
    norm_map = {}

    df = lex_df[[CL1_WORD_COL, CL1_ROOT_COL]].dropna().copy()
    df[CL1_WORD_COL] = df[CL1_WORD_COL].astype(str).str.strip()
    df[CL1_ROOT_COL] = df[CL1_ROOT_COL].astype(str).str.strip()

    for w, r in zip(df[CL1_WORD_COL], df[CL1_ROOT_COL]):
        exact_map[w] = r
        nw = normalize_arabic(w)
        if nw and nw not in norm_map:
            norm_map[nw] = r

    return exact_map, norm_map

@st.cache_data(show_spinner=True)
def index_ayah_roots(df: pd.DataFrame, exact_map: dict, norm_map: dict):
    roots_sets = []
    for _, row in df.iterrows():
        text_t = str(row.get(COL_TASH, "") or "")
        text_p = str(row.get(COL_PLAIN, "") or "")

        roots = set()

        for tok in tokenize(text_t):
            if tok in exact_map:
                roots.add(exact_map[tok])
            else:
                nt = normalize_arabic(tok)
                if nt in norm_map:
                    roots.add(norm_map[nt])

        for tok in tokenize(text_p):
            nt = normalize_arabic(tok)
            if nt in norm_map:
                roots.add(norm_map[nt])

        roots_sets.append(roots)

    return roots_sets

def format_surah_title(display_mode: str, sur_t: str, sur_p: str) -> str:
    if display_mode == "بالتشكيل":
        return sur_t
    if display_mode == "بدون تشكيل":
        return sur_p
    return f"{sur_t} / {sur_p}"

def pick_text(display_mode: str, t: str, p: str) -> str:
    if display_mode == "بالتشكيل":
        return t
    if display_mode == "بدون تشكيل":
        return p
    return f"{t}\n{p}"

# =======================
# واجهة Streamlit
# =======================
st.set_page_config(page_title="سياق الجذر", page_icon="🧩", layout="wide")
st.title("🧩 سياق الجذر (قبل / الآية / بعد)")

# إعدادات العرض (مفيدة للمستخدم)
c_set1, c_set2, c_set3 = st.columns(3)
with c_set1:
    display_mode = st.radio("عرض النص", ["بالتشكيل", "بدون تشكيل", "كلاهما"], index=2)
with c_set2:
    prev_n = st.number_input("عدد الآيات السابقة", min_value=0, max_value=50, value=3)
with c_set3:
    next_n = st.number_input("عدد الآيات اللاحقة", min_value=0, max_value=50, value=3)

# تحميل الملفات (بدون تدخل المستخدم)
try:
    quran_df_raw = load_quran_csv(CSV_PATH)
    lex_df_raw = load_xlsx(CL1_PATH)
except Exception as e:
    st.error(f"فشل تحميل البيانات الأساسية:\n{e}")
    st.stop()

# فحص الأعمدة الحرجة
required_cols = [COL_TASH, COL_PLAIN, COL_SURAH_NO, COL_AYAH_NO, COL_SURAH_T, COL_SURAH_P]
if not all(c in quran_df_raw.columns for c in required_cols):
    st.error("ملف CSV لا يطابق البنية المتوقعة. راجع الثوابت أعلى الملف.")
    st.stop()

# بناء القواميس + فهرسة الجذور
exact_map, norm_map = build_root_maps(lex_df_raw)

quran_df = quran_df_raw.copy()
quran_df["_roots_set"] = index_ayah_roots(quran_df, exact_map, norm_map)

# =======================
# البحث
# =======================
c1, c2 = st.columns([3, 1])
with c1:
    root_query = st.text_input("أدخل الجذر", placeholder="مثال: خرر")
with c2:
    run = st.button("🔎 بحث", type="primary", use_container_width=True)

if run or root_query.strip():
    rq = root_query.strip()
    if not rq:
        st.stop()

    rq_norm = normalize_arabic(rq)

    def has_root(rs):
        return rq_norm in {normalize_arabic(x) for x in rs}

    hits = quran_df[quran_df["_roots_set"].apply(has_root)].copy()

    hits["_s"] = hits[COL_SURAH_NO].map(safe_int)
    hits["_a"] = hits[COL_AYAH_NO].map(safe_int)
    hits = hits.sort_values(["_s", "_a"]).reset_index(drop=True)

    total = len(hits)
    st.subheader("النتائج")
    st.write(f"عدد الآيات المطابقة للجذر **{rq}**: **{total}**")

    if total == 0:
        st.stop()

    # ترتيب المصحف الكامل للسياق
    q_all = quran_df.copy()
    q_all["_s"] = q_all[COL_SURAH_NO].map(safe_int)
    q_all["_a"] = q_all[COL_AYAH_NO].map(safe_int)
    q_all = q_all.sort_values(["_s", "_a"]).reset_index(drop=True)

    index_map = {
        (str(r[COL_SURAH_NO]), str(r[COL_AYAH_NO])): i
        for i, r in q_all.iterrows()
    }

    ctx_rows = []

    for _, hit in hits.iterrows():
        key = (str(hit[COL_SURAH_NO]), str(hit[COL_AYAH_NO]))
        idx = index_map.get(key)
        if idx is None:
            continue

        start = max(0, idx - prev_n)
        end = min(len(q_all) - 1, idx + next_n)

        sur_title = format_surah_title(
            display_mode,
            hit[COL_SURAH_T],
            hit[COL_SURAH_P]
        )

        before, after = [], []

        for j in range(start, idx):
            r = q_all.iloc[j]
            before.append(f"({r[COL_SURAH_NO]}:{r[COL_AYAH_NO]}) {pick_text(display_mode, r[COL_TASH], r[COL_PLAIN])}")

        center = pick_text(display_mode, hit[COL_TASH], hit[COL_PLAIN])

        for j in range(idx + 1, end + 1):
            r = q_all.iloc[j]
            after.append(f"({r[COL_SURAH_NO]}:{r[COL_AYAH_NO]}) {pick_text(display_mode, r[COL_TASH], r[COL_PLAIN])}")

        st.markdown(f"### [{hit[COL_SURAH_NO]}:{hit[COL_AYAH_NO]}] {sur_title}")
        st.markdown("**قبل:**" if before else "**قبل:** لا يوجد")
        for b in before:
            st.markdown(f"- {b}")

        st.markdown("**الآية المطابقة:**")
        st.markdown(f"- **{center}**")

        st.markdown("**بعد:**" if after else "**بعد:** لا يوجد")
        for a in after:
            st.markdown(f"- {a}")

        st.divider()

        ctx_rows.append({
            "root": rq_norm,
            "surah_no": hit[COL_SURAH_NO],
            "ayah_no": hit[COL_AYAH_NO],
            "surah": sur_title,
            "prev_n": prev_n,
            "next_n": next_n,
            "before": " | ".join(before),
            "center": center,
            "after": " | ".join(after),
        })

    if ctx_rows:
        export_df = pd.DataFrame(ctx_rows)
        st.download_button(
            "⬇️ تنزيل نتائج السياق CSV",
            data=export_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"context_root_{rq_norm}_p{prev_n}_n{next_n}.csv",
            mime="text/csv",
        )

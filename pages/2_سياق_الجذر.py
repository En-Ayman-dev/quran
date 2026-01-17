# pages/2_سياق_الجذر.py
# -*- coding: utf-8 -*-

import re
import pandas as pd
import streamlit as st

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

@st.cache_data(show_spinner=False)
def load_quran_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype=str, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path, dtype=str, encoding="utf-8-sig")

@st.cache_data(show_spinner=False)
def load_lexicon_xlsx(path: str) -> pd.DataFrame:
    return pd.read_excel(path, dtype=str)

@st.cache_data(show_spinner=False)
def build_root_maps(lex_df: pd.DataFrame, word_col: str, root_col: str):
    exact_map = {}
    norm_map = {}

    df = lex_df[[word_col, root_col]].dropna().copy()
    df[word_col] = df[word_col].astype(str).str.strip()
    df[root_col] = df[root_col].astype(str).str.strip()

    for w, r in zip(df[word_col], df[root_col]):
        if not w or not r:
            continue
        exact_map[w] = r
        nw = normalize_arabic(w)
        if nw and nw not in norm_map:
            norm_map[nw] = r

    return exact_map, norm_map

@st.cache_data(show_spinner=True)
def index_ayah_roots(df: pd.DataFrame, col_tash: str, col_plain: str, exact_map: dict, norm_map: dict):
    roots_sets = []
    for _, row in df.iterrows():
        text_t = str(row.get(col_tash, "") or "")
        text_p = str(row.get(col_plain, "") or "")

        tokens_t = tokenize(text_t)
        tokens_p = tokenize(text_p)

        roots = set()

        for tok in tokens_t:
            tok = tok.strip()
            if not tok:
                continue
            if tok in exact_map:
                roots.add(exact_map[tok])
                continue
            ntok = normalize_arabic(tok)
            if ntok in norm_map:
                roots.add(norm_map[ntok])

        for tok in tokens_p:
            tok = tok.strip()
            if not tok:
                continue
            ntok = normalize_arabic(tok)
            if ntok in norm_map:
                roots.add(norm_map[ntok])

        roots_sets.append(roots)

    return roots_sets

def safe_int(x):
    try:
        return int(str(x))
    except Exception:
        return 10**9

def format_surah_title(display_mode: str, sur_t: str, sur_p: str) -> str:
    sur_t = str(sur_t or "")
    sur_p = str(sur_p or "")
    if display_mode == "بالتشكيل":
        return sur_t
    if display_mode == "بدون تشكيل":
        return sur_p
    return f"{sur_t} / {sur_p}"

def pick_text(display_mode: str, t: str, p: str) -> str:
    t = str(t or "")
    p = str(p or "")
    if display_mode == "بالتشكيل":
        return t
    if display_mode == "بدون تشكيل":
        return p
    return f"{t}\n{p}"

st.set_page_config(page_title="سياق الجذر", page_icon="🧩", layout="wide")
st.title("🧩 سياق الجذر (قبل/الآية/بعد)")

with st.sidebar:
    st.header("الملفات")
    csv_path = st.text_input("ملف القرآن CSV", value="quran_corrected_global.csv")
    xlsx_path = st.text_input("قاموس الكلمات والجذور (Cl1.xlsx)", value="Cl1.xlsx")

# تحميل CSV
try:
    quran_df_raw = load_quran_csv(csv_path)
except Exception as e:
    st.error(f"فشل تحميل CSV: {e}")
    st.stop()

csv_cols = list(quran_df_raw.columns)

with st.sidebar:
    st.subheader("تعيين أعمدة CSV")
    def default_idx(name, fallback=0):
        return csv_cols.index(name) if name in csv_cols else fallback

    col_tash = st.selectbox("عمود الآية بالتشكيل", csv_cols, index=default_idx("3", min(3, len(csv_cols)-1)))
    col_plain = st.selectbox("عمود الآية بدون تشكيل", csv_cols, index=default_idx("4", min(4, len(csv_cols)-1)))
    col_surah_no = st.selectbox("عمود رقم السورة", csv_cols, index=default_idx("1", min(1, len(csv_cols)-1)))
    col_ayah_no  = st.selectbox("عمود رقم الآية", csv_cols, index=default_idx("2", min(2, len(csv_cols)-1)))
    col_surah_t  = st.selectbox("عمود اسم السورة (بالتشكيل)", csv_cols, index=default_idx("10", min(10, len(csv_cols)-1)))
    col_surah_p  = st.selectbox("عمود اسم السورة (بدون تشكيل)", csv_cols, index=default_idx("11", min(11, len(csv_cols)-1)))

    st.divider()
    display_mode = st.radio("عرض النص", ["بالتشكيل", "بدون تشكيل", "كلاهما"], index=2)

    st.subheader("السياق")
    prev_n = st.number_input("عدد الآيات السابقة", min_value=0, max_value=50, value=3, step=1)
    next_n = st.number_input("عدد الآيات اللاحقة", min_value=0, max_value=50, value=3, step=1)

# تحميل XLSX
try:
    lex_df_raw = load_lexicon_xlsx(xlsx_path)
except Exception as e:
    st.error(f"فشل تحميل Cl1.xlsx: {e}")
    st.stop()

xlsx_cols = list(lex_df_raw.columns)

with st.sidebar:
    st.subheader("تعيين أعمدة Cl1.xlsx")
    word_col = st.selectbox("عمود الكلمة", xlsx_cols, index=(xlsx_cols.index("الكلمة") if "الكلمة" in xlsx_cols else 0))
    root_col = st.selectbox("عمود الجذر", xlsx_cols, index=(xlsx_cols.index("الجذر") if "الجذر" in xlsx_cols else min(1, len(xlsx_cols)-1)))

# بناء القواميس + الفهرسة
exact_map, norm_map = build_root_maps(lex_df_raw, word_col, root_col)

quran_df = quran_df_raw.copy()
quran_df["_roots_set"] = index_ayah_roots(quran_df, col_tash, col_plain, exact_map, norm_map)

# بحث
c1, c2 = st.columns([2.5, 1])
with c1:
    root_query = st.text_input("أدخل الجذر", placeholder="مثال: رحم")
with c2:
    run = st.button("🔎 بحث", type="primary", use_container_width=True)

if run or root_query.strip():
    rq = root_query.strip()
    if not rq:
        st.stop()

    rq_norm = normalize_arabic(rq)

    def has_root(rootset):
        return rq_norm in {normalize_arabic(x) for x in (rootset or set())}

    hits = quran_df[quran_df["_roots_set"].apply(has_root)].copy()

    # ترتيب
    hits["_s"] = hits[col_surah_no].map(safe_int)
    hits["_a"] = hits[col_ayah_no].map(safe_int)
    hits = hits.sort_values(["_s", "_a"]).drop(columns=["_s", "_a"], errors="ignore").reset_index(drop=True)

    total = len(hits)
    st.subheader("النتائج")
    st.write(f"عدد الآيات المطابقة للجذر **{rq}**: **{total}**")

    if total == 0:
        st.stop()

    # عمل “سياق” لكل نتيجة
    ctx_rows = []
    q_all = quran_df.reset_index(drop=True)

    # حتى يكون السياق صحيح لازم نضمن أن ترتيب CSV نفسه حسب (سورة/آية)
    q_all["_s"] = q_all[col_surah_no].map(safe_int)
    q_all["_a"] = q_all[col_ayah_no].map(safe_int)
    q_all = q_all.sort_values(["_s", "_a"]).drop(columns=["_s", "_a"], errors="ignore").reset_index(drop=True)

    # خريطة من (سورة, آية) -> index داخل q_all
    key_to_idx = {}
    for i, r in q_all.iterrows():
        key_to_idx[(str(r.get(col_surah_no, "")), str(r.get(col_ayah_no, "")))] = i

    for _, hit in hits.iterrows():
        s_no = str(hit.get(col_surah_no, ""))
        a_no = str(hit.get(col_ayah_no, ""))
        idx = key_to_idx.get((s_no, a_no))
        if idx is None:
            continue

        start = max(0, idx - int(prev_n))
        end   = min(len(q_all) - 1, idx + int(next_n))

        # عنوان السورة
        sur_title = format_surah_title(display_mode, hit.get(col_surah_t, ""), hit.get(col_surah_p, ""))

        # تجميع نصوص قبل/بعد
        before = []
        after  = []

        for j in range(start, idx):
            r = q_all.iloc[j]
            before.append({
                "surah_no": r.get(col_surah_no, ""),
                "ayah_no": r.get(col_ayah_no, ""),
                "text": pick_text(display_mode, r.get(col_tash, ""), r.get(col_plain, ""))
            })

        center_text = pick_text(display_mode, hit.get(col_tash, ""), hit.get(col_plain, ""))

        for j in range(idx + 1, end + 1):
            r = q_all.iloc[j]
            after.append({
                "surah_no": r.get(col_surah_no, ""),
                "ayah_no": r.get(col_ayah_no, ""),
                "text": pick_text(display_mode, r.get(col_tash, ""), r.get(col_plain, ""))
            })

        # عرض بصري واضح
        st.markdown(f"### [{s_no}:{a_no}] {sur_title}")

        if before:
            st.markdown("**قبل:**")
            for b in before:
                st.markdown(f"- ({b['surah_no']}:{b['ayah_no']}) {b['text']}")
        else:
            st.markdown("**قبل:** لا يوجد")

        st.markdown("**الآية المطابقة:**")
        st.markdown(f"- **({s_no}:{a_no})** {center_text}")

        if after:
            st.markdown("**بعد:**")
            for a in after:
                st.markdown(f"- ({a['surah_no']}:{a['ayah_no']}) {a['text']}")
        else:
            st.markdown("**بعد:** لا يوجد")

        st.divider()

        # صف للتصدير
        ctx_rows.append({
            "root": rq_norm,
            "surah_no": s_no,
            "ayah_no": a_no,
            "surah": sur_title,
            "prev_n": int(prev_n),
            "next_n": int(next_n),
            "before": " | ".join([f"({x['surah_no']}:{x['ayah_no']}) {x['text']}" for x in before]),
            "center": f"({s_no}:{a_no}) {center_text}",
            "after":  " | ".join([f"({x['surah_no']}:{x['ayah_no']}) {x['text']}" for x in after]),
        })

    # تنزيل النتائج
    if ctx_rows:
        export_df = pd.DataFrame(ctx_rows)
        st.download_button(
            "⬇️ تنزيل نتائج السياق CSV",
            data=export_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"context_root_{rq_norm}_p{int(prev_n)}_n{int(next_n)}.csv",
            mime="text/csv",
        )

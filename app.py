# # app.py
# # -*- coding: utf-8 -*-

# import re
# import pandas as pd
# import streamlit as st

# # =======================
# # تطبيع/تنظيف عربي
# # =======================
# ARABIC_DIACRITICS_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")

# def normalize_arabic(text: str) -> str:
#     """تطبيع عربي (إزالة تشكيل + توحيد بعض الحروف) لتقليل اختلافات الكتابة."""
#     if not isinstance(text, str):
#         return ""
#     t = ARABIC_DIACRITICS_RE.sub("", text)
#     t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
#     t = t.replace("ٱ", "ا")
#     t = t.replace("ة", "ه")
#     t = t.replace("ى", "ي")
#     t = t.replace("ؤ", "و").replace("ئ", "ي")
#     t = re.sub(r"\s+", " ", t).strip()
#     return t

# TOKEN_RE = re.compile(r"[^\s]+")

# def tokenize(text: str):
#     if not isinstance(text, str) or not text:
#         return []
#     return TOKEN_RE.findall(text)

# # =======================
# # تحميل البيانات
# # =======================
# @st.cache_data(show_spinner=False)
# def load_quran_csv(path: str) -> pd.DataFrame:
#     try:
#         return pd.read_csv(path, dtype=str, encoding="utf-8")
#     except UnicodeDecodeError:
#         return pd.read_csv(path, dtype=str, encoding="utf-8-sig")

# @st.cache_data(show_spinner=False)
# def load_lexicon_xlsx(path: str) -> pd.DataFrame:
#     return pd.read_excel(path, dtype=str)  # يحتاج openpyxl

# @st.cache_data(show_spinner=False)
# def build_root_maps(lex_df: pd.DataFrame, word_col: str, root_col: str):
#     """
#     قاموسان:
#     1) exact_map: مطابقة حرفية للكلمة (كما هي بالتشكيل)
#     2) norm_map : مطابقة بعد التطبيع/إزالة التشكيل
#     """
#     exact_map = {}
#     norm_map = {}

#     df = lex_df[[word_col, root_col]].dropna().copy()
#     df[word_col] = df[word_col].astype(str).str.strip()
#     df[root_col] = df[root_col].astype(str).str.strip()

#     for w, r in zip(df[word_col], df[root_col]):
#         if not w or not r:
#             continue
#         exact_map[w] = r
#         nw = normalize_arabic(w)
#         if nw and nw not in norm_map:
#             norm_map[nw] = r

#     return exact_map, norm_map

# @st.cache_data(show_spinner=True)
# def index_ayah_roots(df: pd.DataFrame, col_tash: str, col_plain: str, exact_map: dict, norm_map: dict):
#     """
#     يبني:
#     - roots_set: مجموعة جذور الكلمات التي تم التعرف عليها في الآية
#     - coverage: نسبة الكلمات التي وُجد لها جذر (تقدير)
#     """
#     roots_sets = []
#     coverages = []

#     for _, row in df.iterrows():
#         text_t = str(row.get(col_tash, "") or "")
#         text_p = str(row.get(col_plain, "") or "")

#         tokens_t = tokenize(text_t)
#         tokens_p = tokenize(text_p)

#         roots = set()
#         known = 0
#         total = 0

#         # 1) من النص بالتشكيل: مطابقة دقيقة ثم مطبّعة
#         for tok in tokens_t:
#             tok = tok.strip()
#             if not tok:
#                 continue
#             total += 1

#             if tok in exact_map:
#                 roots.add(exact_map[tok])
#                 known += 1
#                 continue

#             ntok = normalize_arabic(tok)
#             if ntok in norm_map:
#                 roots.add(norm_map[ntok])
#                 known += 1
#                 continue

#         # 2) تعزيز من النص بدون تشكيل (لا نزيد total)
#         for tok in tokens_p:
#             tok = tok.strip()
#             if not tok:
#                 continue
#             ntok = normalize_arabic(tok)
#             if ntok in norm_map:
#                 roots.add(norm_map[ntok])

#         coverage = (known / total) if total else 0.0
#         roots_sets.append(roots)
#         coverages.append(coverage)

#     return roots_sets, coverages

# def safe_int(x):
#     try:
#         return int(str(x))
#     except Exception:
#         return 10**9

# # =======================
# # واجهة Streamlit
# # =======================
# st.set_page_config(page_title="بحث بالجذر (Cl1 + CSV)", page_icon="📖", layout="wide")

# # CSS احترافي: يدعم dark/light ويضمن تباين النص مع البطاقات
# st.markdown("""
# <style>
# :root { --card-radius: 16px; }

# .qcard{
#   border-radius: var(--card-radius);
#   padding: 16px 16px 12px 16px;
#   margin: 12px 0;
#   border: 1px solid rgba(0,0,0,0.08);
#   box-shadow: 0 6px 18px rgba(0,0,0,0.06);
#   direction: rtl;
# }

# @media (prefers-color-scheme: light) {
#   .qcard{ background: #ffffff; color: #111111; border-color: rgba(0,0,0,0.08); }
#   .qmuted{ color: rgba(0,0,0,0.60); }
#   .qmeta{ color: rgba(0,0,0,0.70); }
# }

# @media (prefers-color-scheme: dark) {
#   .qcard{
#     background: #151515;
#     color: #f2f2f2;
#     border-color: rgba(255,255,255,0.14);
#     box-shadow: 0 6px 18px rgba(0,0,0,0.30);
#   }
#   .qmuted{ color: rgba(255,255,255,0.70); }
#   .qmeta{ color: rgba(255,255,255,0.75); }
# }

# .qhead{ font-weight: 750; font-size: 16px; margin-bottom: 10px; }
# .qayah{ font-size: 22px; line-height: 1.9; margin: 0; }
# .qsp{ height: 10px; }
# .qbadge{
#   display: inline-block;
#   padding: 4px 10px;
#   border-radius: 999px;
#   font-size: 12px;
#   margin-top: 10px;
#   border: 1px solid rgba(127,127,127,0.25);
# }
# </style>
# """, unsafe_allow_html=True)

# st.title("📖 بحث الآيات بالجذر (باستخدام Cl1.xlsx)")

# with st.sidebar:
#     st.header("الملفات")
#     csv_path = st.text_input("ملف القرآن CSV", value="quran_corrected_global.csv")
#     xlsx_path = st.text_input("قاموس الكلمات والجذور (Cl1.xlsx)", value="Cl1.xlsx")

# # تحميل CSV لعرض أعمدته كقوائم
# try:
#     quran_df_raw = load_quran_csv(csv_path)
# except Exception as e:
#     st.error(f"فشل تحميل CSV: {e}")
#     st.stop()

# csv_cols = list(quran_df_raw.columns)

# with st.sidebar:
#     st.subheader("تعيين أعمدة CSV (اختر من القائمة)")
#     def default_idx(name, fallback=0):
#         return csv_cols.index(name) if name in csv_cols else fallback

#     col_tash = st.selectbox("عمود الآية بالتشكيل", csv_cols, index=default_idx("3", min(3, len(csv_cols)-1)))
#     col_plain = st.selectbox("عمود الآية بدون تشكيل", csv_cols, index=default_idx("4", min(4, len(csv_cols)-1)))
#     col_surah_no = st.selectbox("عمود رقم السورة", csv_cols, index=default_idx("1", min(1, len(csv_cols)-1)))
#     col_ayah_no  = st.selectbox("عمود رقم الآية", csv_cols, index=default_idx("2", min(2, len(csv_cols)-1)))
#     col_surah_t  = st.selectbox("عمود اسم السورة (بالتشكيل)", csv_cols, index=default_idx("10", min(10, len(csv_cols)-1)))
#     col_surah_p  = st.selectbox("عمود اسم السورة (بدون تشكيل)", csv_cols, index=default_idx("11", min(11, len(csv_cols)-1)))

# # تحميل XLSX
# try:
#     lex_df_raw = load_lexicon_xlsx(xlsx_path)
# except Exception as e:
#     st.error(f"فشل تحميل Cl1.xlsx: {e}")
#     st.stop()

# xlsx_cols = list(lex_df_raw.columns)

# with st.sidebar:
#     st.subheader("تعيين أعمدة Cl1.xlsx")
#     word_col = st.selectbox("عمود الكلمة", xlsx_cols, index=(xlsx_cols.index("الكلمة") if "الكلمة" in xlsx_cols else 0))
#     root_col = st.selectbox("عمود الجذر", xlsx_cols, index=(xlsx_cols.index("الجذر") if "الجذر" in xlsx_cols else min(1, len(xlsx_cols)-1)))

#     st.divider()
#     display_mode = st.radio("عرض النتائج", ["بالتشكيل", "بدون تشكيل", "كلاهما"], index=2)
#     page_size = st.slider("عدد النتائج في الصفحة", 10, 200, 50, step=10)

# # بناء القواميس
# try:
#     exact_map, norm_map = build_root_maps(lex_df_raw, word_col, root_col)
# except Exception as e:
#     st.error(f"فشل بناء القاموس من Cl1.xlsx: {e}")
#     st.stop()

# # st.caption(f"القاموس: مطابقات دقيقة={len(exact_map):,} | مطابقات بعد التطبيع={len(norm_map):,}")

# # فهرسة الجذور لكل آية
# quran_df = quran_df_raw.copy()
# roots_sets, coverages = index_ayah_roots(quran_df, col_tash, col_plain, exact_map, norm_map)
# quran_df["_roots_set"] = roots_sets
# quran_df["_coverage"] = coverages

# avg_cov = float(quran_df["_coverage"].mean())
# # st.info(f"متوسط تغطية القاموس (تقديري): {avg_cov:.1%} — إذا كانت منخفضة فالقاموس لا يغطي كلمات CSV بالكامل أو توجد اختلافات كتابة.")

# # البحث
# c1, c2, c3, c4 = st.columns([2.2, 1, 1, 1])
# with c1:
#     root_query = st.text_input("أدخل الجذر للبحث", placeholder="مثال: رحم")
# with c2:
#     surah_filter = st.text_input("رقم السورة (اختياري)", placeholder="مثال: 1")
# with c3:
#     ayah_filter = st.text_input("رقم الآية (اختياري)", placeholder="مثال: 7")
# with c4:
#     run = st.button("🔎 بحث", type="primary", use_container_width=True)

# if run or root_query.strip():
#     rq = root_query.strip()
#     if not rq:
#         st.stop()

#     rq_norm = normalize_arabic(rq)

#     def has_root(rootset):
#         return rq_norm in {normalize_arabic(x) for x in (rootset or set())}

#     hits = quran_df[quran_df["_roots_set"].apply(has_root)].copy()

#     if surah_filter.strip():
#         hits = hits[hits[col_surah_no].astype(str) == surah_filter.strip()]
#     if ayah_filter.strip():
#         hits = hits[hits[col_ayah_no].astype(str) == ayah_filter.strip()]

#     total = len(hits)
#     st.subheader("النتائج")
#     st.write(f"عدد الآيات التي ظهر فيها الجذر **{rq}**: **{total}**")

#     if total == 0:
#         st.stop()

#     hits["_s"] = hits[col_surah_no].map(safe_int)
#     hits["_a"] = hits[col_ayah_no].map(safe_int)
#     hits = hits.sort_values(["_s", "_a"]).drop(columns=["_s", "_a"], errors="ignore")

#     pages = (total + page_size - 1) // page_size
#     page = st.number_input("الصفحة", min_value=1, max_value=pages, value=1, step=1)
#     start = (page - 1) * page_size
#     end = min(start + page_size, total)
#     view = hits.iloc[start:end]

#     # ======== التعديل المطلوب هنا: العرض ينطبق على أسماء السور أيضًا ========
#     def format_surah_title(sur_t: str, sur_p: str) -> str:
#         sur_t = str(sur_t or "")
#         sur_p = str(sur_p or "")
#         if display_mode == "بالتشكيل":
#             return sur_t
#         if display_mode == "بدون تشكيل":
#             return sur_p
#         # كلاهما
#         return f"{sur_t} / {sur_p}"

#     for _, row in view.iterrows():
#         sur_no = row.get(col_surah_no, "")
#         ay_no  = row.get(col_ayah_no, "")

#         sur_t  = row.get(col_surah_t, "")
#         sur_p  = row.get(col_surah_p, "")

#         ay_t   = str(row.get(col_tash, "") or "")
#         ay_p   = str(row.get(col_plain, "") or "")

#         cov = float(row.get("_coverage", 0.0)) * 100.0

#         sur_title = format_surah_title(sur_t, sur_p)

#         header_html = f"<div class='qhead'>[{sur_no}:{ay_no}] {sur_title}</div>"

#         if display_mode == "بالتشكيل":
#             body_html = f"<p class='qayah'>{ay_t}</p>"
#         elif display_mode == "بدون تشكيل":
#             body_html = f"<p class='qayah'>{ay_p}</p>"
#         else:
#             body_html = (
#                 "<div class='qmuted' style='font-size:13px;margin-bottom:4px;'>بالتشكيل</div>"
#                 f"<p class='qayah'>{ay_t}</p>"
#                 "<div class='qsp'></div>"
#                 "<div class='qmuted' style='font-size:13px;margin-bottom:4px;'>بدون تشكيل</div>"
#                 f"<p class='qayah'>{ay_p}</p>"
#             )

#         card_html = f"""
#         <div class="qcard">
#           {header_html}
#           {body_html}
#           <div class="qbadge qmeta">تغطية القاموس في هذه الآية (تقديري): {cov:.1f}%</div>
#         </div>
#         """

#         st.markdown(card_html, unsafe_allow_html=True)

#     st.caption(f"عرض النتائج {start+1} إلى {end} من {total} — صفحة {page} من {pages}")

# # ======================
# # تصدير CSV حسب وضع العرض
# # ======================
#     st.divider()

#     base_cols = [col_surah_no, col_ayah_no]
#     export_df = hits[base_cols].copy()
#     export_df.columns = ["surah_no", "ayah_no"]

#     if display_mode == "بالتشكيل":
#         export_df["surah"] = hits[col_surah_t]
#         export_df["ayah"]  = hits[col_tash]

#     elif display_mode == "بدون تشكيل":
#         export_df["surah"] = hits[col_surah_p]
#         export_df["ayah"]  = hits[col_plain]

#     else:  # كلاهما
#         export_df["surah_tashkeel"] = hits[col_surah_t]
#         export_df["surah_plain"]    = hits[col_surah_p]
#         export_df["ayah_tashkeel"]  = hits[col_tash]
#         export_df["ayah_plain"]     = hits[col_plain]

#     st.download_button(
#         "⬇️ تنزيل النتائج CSV",
#         data=export_df.to_csv(index=False).encode("utf-8-sig"),
#         file_name=f"results_root_{rq_norm}_{display_mode}.csv",
#         mime="text/csv",
#     )
# app.py
# -*- coding: utf-8 -*-

import re
import pandas as pd
import streamlit as st

# =======================
# إعدادات ثابتة (مخفية عن المستخدم)
# غيّرها هنا فقط إذا تغيّر CSV أو أسماء الأعمدة
# =======================
CSV_PATH = "quran_corrected_global.csv"
CL1_PATH = "Cl1.xlsx"
GROUPED_PATH = "Cl1_grouped_by_root.xlsx"

# أسماء الأعمدة/الفهارس داخل CSV (حسب ملفك)
COL_TASH = "3"       # عمود الآية بالتشكيل
COL_PLAIN = "4"      # عمود الآية بدون تشكيل
COL_SURAH_NO = "1"   # رقم السورة
COL_AYAH_NO = "2"    # رقم الآية
COL_SURAH_T = "10"   # اسم السورة (بالتشكيل)
COL_SURAH_P = "11"   # اسم السورة (بدون تشكيل)

# أعمدة Cl1.xlsx
CL1_WORD_COL = "الكلمة"
CL1_ROOT_COL = "الجذر"

# أعمدة Cl1_grouped_by_root.xlsx
G_ROOT_COL = "الجذر"
G_WORD_COL = "الكلمة"
G_COUNT_COL = "عدد_ذكر_الكلمة"


# =======================
# تطبيع/تنظيف عربي
# =======================
ARABIC_DIACRITICS_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
TOKEN_RE = re.compile(r"[^\s]+")

def normalize_arabic(text: str) -> str:
    """تطبيع عربي (إزالة تشكيل + توحيد بعض الحروف) لتقليل اختلافات الكتابة."""
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
    return pd.read_excel(path, dtype=str)  # يحتاج openpyxl

@st.cache_data(show_spinner=False)
def build_root_maps(lex_df: pd.DataFrame, word_col: str, root_col: str):
    """
    قاموسان:
    1) exact_map: مطابقة حرفية للكلمة (كما هي بالتشكيل)
    2) norm_map : مطابقة بعد التطبيع/إزالة التشكيل
    """
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
    coverages = []

    for _, row in df.iterrows():
        text_t = str(row.get(col_tash, "") or "")
        text_p = str(row.get(col_plain, "") or "")

        tokens_t = tokenize(text_t)
        tokens_p = tokenize(text_p)

        roots = set()
        known = 0
        total = 0

        # 1) من النص بالتشكيل: مطابقة دقيقة ثم مطبّعة
        for tok in tokens_t:
            tok = tok.strip()
            if not tok:
                continue
            total += 1

            if tok in exact_map:
                roots.add(exact_map[tok])
                known += 1
                continue

            ntok = normalize_arabic(tok)
            if ntok in norm_map:
                roots.add(norm_map[ntok])
                known += 1
                continue

        # 2) تعزيز من النص بدون تشكيل (لا نزيد total)
        for tok in tokens_p:
            tok = tok.strip()
            if not tok:
                continue
            ntok = normalize_arabic(tok)
            if ntok in norm_map:
                roots.add(norm_map[ntok])

        coverage = (known / total) if total else 0.0
        roots_sets.append(roots)
        coverages.append(coverage)

    return roots_sets, coverages


# =======================
# واجهة Streamlit
# =======================
st.set_page_config(page_title="بحث بالجذر", page_icon="📖", layout="wide")

# CSS احترافي: يدعم dark/light ويضمن تباين النص مع البطاقات
st.markdown("""
<style>
:root { --card-radius: 16px; }

.qcard{
  border-radius: var(--card-radius);
  padding: 16px 16px 12px 16px;
  margin: 12px 0;
  border: 1px solid rgba(0,0,0,0.08);
  box-shadow: 0 6px 18px rgba(0,0,0,0.06);
  direction: rtl;
}

@media (prefers-color-scheme: light) {
  .qcard{ background: #ffffff; color: #111111; border-color: rgba(0,0,0,0.08); }
  .qmuted{ color: rgba(0,0,0,0.60); }
  .qmeta{ color: rgba(0,0,0,0.70); }
}

@media (prefers-color-scheme: dark) {
  .qcard{
    background: #151515;
    color: #f2f2f2;
    border-color: rgba(255,255,255,0.14);
    box-shadow: 0 6px 18px rgba(0,0,0,0.30);
  }
  .qmuted{ color: rgba(255,255,255,0.70); }
  .qmeta{ color: rgba(255,255,255,0.75); }
}

.qhead{ font-weight: 750; font-size: 16px; margin-bottom: 10px; }
.qayah{ font-size: 22px; line-height: 1.9; margin: 0; }
.qsp{ height: 10px; }
.qbadge{
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  margin-top: 10px;
  border: 1px solid rgba(127,127,127,0.25);
}
</style>
""", unsafe_allow_html=True)

st.title("📖 بحث الآيات بالجذر")

with st.sidebar:
    st.subheader("إعدادات العرض")
    display_mode = st.radio("عرض النتائج", ["بالتشكيل", "بدون تشكيل", "كلاهما"], index=2)
    page_size = st.slider("عدد النتائج في الصفحة", 10, 200, 50, step=10)

# تحميل الملفات (بدون أي خيارات للمستخدم)
try:
    quran_df_raw = load_quran_csv(CSV_PATH)
except Exception as e:
    st.error(f"فشل تحميل ملف CSV: {CSV_PATH}\n\nالتفاصيل: {e}")
    st.stop()

try:
    lex_df_raw = load_xlsx(CL1_PATH)
except Exception as e:
    st.error(f"فشل تحميل ملف Cl1.xlsx: {CL1_PATH}\n\nالتفاصيل: {e}")
    st.stop()

# grouped اختياري (لو فشل لا يوقف التطبيق)
group_df_raw = None
try:
    group_df_raw = load_xlsx(GROUPED_PATH)
except Exception:
    group_df_raw = None

# تحقق سريع من وجود الأعمدة الأساسية (بدون واجهة)
required_csv_cols = [COL_TASH, COL_PLAIN, COL_SURAH_NO, COL_AYAH_NO, COL_SURAH_T, COL_SURAH_P]
missing_csv = [c for c in required_csv_cols if c not in quran_df_raw.columns]
if missing_csv:
    st.error(f"ملف CSV لا يحتوي الأعمدة المتوقعة: {missing_csv}\n"
             f"عدّل الثوابت أعلى الملف (COL_...) لتطابق أعمدة CSV لديك.")
    st.stop()

missing_cl1 = [c for c in [CL1_WORD_COL, CL1_ROOT_COL] if c not in lex_df_raw.columns]
if missing_cl1:
    st.error(f"ملف Cl1.xlsx لا يحتوي الأعمدة المتوقعة: {missing_cl1}\n"
             f"عدّل الثوابت CL1_WORD_COL / CL1_ROOT_COL أعلى الملف.")
    st.stop()

# بناء القواميس + فهرسة الجذور لكل آية
exact_map, norm_map = build_root_maps(lex_df_raw, CL1_WORD_COL, CL1_ROOT_COL)

quran_df = quran_df_raw.copy()
roots_sets, coverages = index_ayah_roots(quran_df, COL_TASH, COL_PLAIN, exact_map, norm_map)
quran_df["_roots_set"] = roots_sets
quran_df["_coverage"] = coverages

# البحث
c1, c2, c3, c4 = st.columns([2.2, 1, 1, 1])
with c1:
    root_query = st.text_input("أدخل الجذر للبحث", placeholder="مثال: رحم")
with c2:
    surah_filter = st.text_input("رقم السورة (اختياري)", placeholder="مثال: 1")
with c3:
    ayah_filter = st.text_input("رقم الآية (اختياري)", placeholder="مثال: 7")
with c4:
    run = st.button("🔎 بحث", type="primary", use_container_width=True)

def format_surah_title(sur_t: str, sur_p: str) -> str:
    sur_t = str(sur_t or "")
    sur_p = str(sur_p or "")
    if display_mode == "بالتشكيل":
        return sur_t
    if display_mode == "بدون تشكيل":
        return sur_p
    return f"{sur_t} / {sur_p}"

if run or root_query.strip():
    rq = root_query.strip()
    if not rq:
        st.stop()

    rq_norm = normalize_arabic(rq)

    def has_root(rootset):
        return rq_norm in {normalize_arabic(x) for x in (rootset or set())}

    hits = quran_df[quran_df["_roots_set"].apply(has_root)].copy()

    if surah_filter.strip():
        hits = hits[hits[COL_SURAH_NO].astype(str) == surah_filter.strip()]
    if ayah_filter.strip():
        hits = hits[hits[COL_AYAH_NO].astype(str) == ayah_filter.strip()]

    total = len(hits)
    st.subheader("النتائج")
    st.write(f"عدد الآيات التي ظهر فيها الجذر **{rq}**: **{total}**")

    if total == 0:
        st.stop()

    # ======================
    # تقرير كلمات الجذر (من grouped file)
    # ======================
    if group_df_raw is not None:
        # لو الأعمدة غير موجودة لا نعرض التقرير
        if all(c in group_df_raw.columns for c in [G_ROOT_COL, G_WORD_COL, G_COUNT_COL]):
            try:
                gdf = group_df_raw[[G_ROOT_COL, G_WORD_COL, G_COUNT_COL]].dropna().copy()
                gdf["_root_norm"] = gdf[G_ROOT_COL].astype(str).map(normalize_arabic)
                rep = gdf[gdf["_root_norm"] == rq_norm].copy()

                rep["count"] = pd.to_numeric(rep[G_COUNT_COL].astype(str).str.strip(), errors="coerce") \
                                  .fillna(0).astype(int)

                rep["word_tashkeel"] = rep[G_WORD_COL].astype(str).str.strip()
                rep["word_plain"] = rep["word_tashkeel"].map(normalize_arabic)

                if display_mode == "بالتشكيل":
                    rep["word"] = rep["word_tashkeel"]
                elif display_mode == "بدون تشكيل":
                    rep["word"] = rep["word_plain"]
                else:
                    rep["word"] = rep["word_tashkeel"] 

                rep = rep[["word", "count"]].sort_values("count", ascending=False).reset_index(drop=True)

                st.markdown("### تقرير كلمات الجذر")
                st.dataframe(rep, use_container_width=True, hide_index=True)

                st.download_button(
                    "⬇️ تنزيل تقرير الكلمات CSV",
                    data=rep.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"root_words_{rq_norm}.csv",
                    mime="text/csv",
                )
                st.divider()
            except Exception as e:
                st.warning(f"تعذر إنشاء تقرير كلمات الجذر: {e}")

    # ترتيب/عرض الآيات
    hits["_s"] = hits[COL_SURAH_NO].map(safe_int)
    hits["_a"] = hits[COL_AYAH_NO].map(safe_int)
    hits = hits.sort_values(["_s", "_a"]).drop(columns=["_s", "_a"], errors="ignore")

    pages = (total + page_size - 1) // page_size
    page = st.number_input("الصفحة", min_value=1, max_value=pages, value=1, step=1)
    start = (page - 1) * page_size
    end = min(start + page_size, total)
    view = hits.iloc[start:end]

    for _, row in view.iterrows():
        sur_no = row.get(COL_SURAH_NO, "")
        ay_no  = row.get(COL_AYAH_NO, "")

        sur_t  = row.get(COL_SURAH_T, "")
        sur_p  = row.get(COL_SURAH_P, "")

        ay_t   = str(row.get(COL_TASH, "") or "")
        ay_p   = str(row.get(COL_PLAIN, "") or "")

        cov = float(row.get("_coverage", 0.0)) * 100.0
        sur_title = format_surah_title(sur_t, sur_p)

        header_html = f"<div class='qhead'>[{sur_no}:{ay_no}] {sur_title}</div>"

        if display_mode == "بالتشكيل":
            body_html = f"<p class='qayah'>{ay_t}</p>"
        elif display_mode == "بدون تشكيل":
            body_html = f"<p class='qayah'>{ay_p}</p>"
        else:
            body_html = (
                "<div class='qmuted' style='font-size:13px;margin-bottom:4px;'>بالتشكيل</div>"
                f"<p class='qayah'>{ay_t}</p>"
                "<div class='qsp'></div>"
                "<div class='qmuted' style='font-size:13px;margin-bottom:4px;'>بدون تشكيل</div>"
                f"<p class='qayah'>{ay_p}</p>"
            )

        card_html = f"""
        <div class="qcard">
          {header_html}
          {body_html}
          <div class="qbadge qmeta">تغطية القاموس في هذه الآية (تقديري): {cov:.1f}%</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

    st.caption(f"عرض النتائج {start+1} إلى {end} من {total} — صفحة {page} من {pages}")

    # ======================
    # تصدير CSV حسب وضع العرض
    # ======================
    st.divider()

    export_df = hits[[COL_SURAH_NO, COL_AYAH_NO]].copy()
    export_df.columns = ["surah_no", "ayah_no"]

    if display_mode == "بالتشكيل":
        export_df["surah"] = hits[COL_SURAH_T]
        export_df["ayah"]  = hits[COL_TASH]
    elif display_mode == "بدون تشكيل":
        export_df["surah"] = hits[COL_SURAH_P]
        export_df["ayah"]  = hits[COL_PLAIN]
    else:
        export_df["surah_tashkeel"] = hits[COL_SURAH_T]
        export_df["surah_plain"]    = hits[COL_SURAH_P]
        export_df["ayah_tashkeel"]  = hits[COL_TASH]
        export_df["ayah_plain"]     = hits[COL_PLAIN]

    st.download_button(
        "⬇️ تنزيل النتائج CSV",
        data=export_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"results_root_{rq_norm}_{display_mode}.csv",
        mime="text/csv",
    )

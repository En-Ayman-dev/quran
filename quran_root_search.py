#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import pandas as pd

# --------- إعدادات افتراضية لأسماء الأعمدة (عدّلها حسب ملفك) ----------
DEFAULT_COL_TASHKEEL = "4"    # في عينتك: العمود 4 = الآية بالتشكيل
DEFAULT_COL_PLAIN    = "5"    # في عينتك: العمود 5 = الآية بدون تشكيل
DEFAULT_COL_SURAH_T  = "12"   # في عينتك: العمود 12 = اسم السورة (بالتشكيل)
DEFAULT_COL_SURAH_P  = "13"   # في عينتك: العمود 13 = اسم السورة (بدون تشكيل)
DEFAULT_COL_AYAH_NO  = "3"    # في عينتك: العمود 3 = رقم الآية داخل السورة
DEFAULT_COL_SURAH_NO = "2"    # في عينتك: العمود 2 = رقم السورة

# خيار متقدم: إن كان لديك عمود جذور للآية نفسها (جذور كلماتها)
# مثال محتوى الخلية: "سمو أله رحم رحم ..."
DEFAULT_COL_ROOTS = None  # ضع اسم العمود هنا إذا كان موجودًا مثل: "roots"


# --------------------- أدوات مساعدة ---------------------
ARABIC_DIACRITICS_RE = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)

def strip_diacritics(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return ARABIC_DIACRITICS_RE.sub("", text)

def normalize_arabic(text: str) -> str:
    """تطبيع بسيط لتقليل اختلافات الألف/الهمزة والتاء المربوطة..."""
    if not isinstance(text, str):
        return ""
    t = text
    t = strip_diacritics(t)
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ٱ", "ا")
    t = t.replace("ة", "ه")
    t = t.replace("ى", "ي")
    t = t.replace("ؤ", "و").replace("ئ", "ي")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def choose_mode() -> str:
    print("\nاختر طريقة عرض الآيات:")
    print("1) بالتشكيل فقط")
    print("2) بدون تشكيل فقط")
    print("3) كلاهما")
    while True:
        x = input("اختيارك (1/2/3): ").strip()
        if x == "1":
            return "tashkeel"
        if x == "2":
            return "plain"
        if x == "3":
            return "both"
        print("قيمة غير صحيحة.")

def build_matcher(root: str, match_mode: str):
    """
    match_mode:
      - 'text': بحث نصي داخل الآية
      - 'roots': بحث داخل عمود جذور الآية (مطابقة جذر كعنصر)
    """
    root_norm = normalize_arabic(root)

    if match_mode == "roots":
        # مطابقة جذر كعنصر مستقل داخل قائمة جذور (مفصول مسافة/فاصلة)
        # نطبع الجذور أيضًا قبل المقارنة
        def f(cell):
            cell_norm = normalize_arabic(str(cell))
            # تقسيم على مسافات أو فواصل
            parts = re.split(r"[,\s]+", cell_norm)
            return root_norm in [p for p in parts if p]
        return f

    # match_mode == "text"
    # نبحث عن تسلسل حروف الجذر داخل النص بعد التطبيع
    pattern = re.compile(re.escape(root_norm))
    def f(text):
        txt_norm = normalize_arabic(str(text))
        return bool(pattern.search(txt_norm))
    return f

def safe_get(row, col):
    try:
        return row[col]
    except Exception:
        return ""

def print_result(row, mode, cols):
    col_tash, col_plain, col_sur_t, col_sur_p, col_sur_no, col_ayah_no = cols

    sur_no = safe_get(row, col_sur_no)
    ay_no  = safe_get(row, col_ayah_no)

    if mode == "tashkeel":
        sur_name = safe_get(row, col_sur_t)
        ay_text  = safe_get(row, col_tash)
        print(f"[{sur_no}:{ay_no}] {sur_name} — {ay_text}")

    elif mode == "plain":
        sur_name = safe_get(row, col_sur_p)
        ay_text  = safe_get(row, col_plain)
        print(f"[{sur_no}:{ay_no}] {sur_name} — {ay_text}")

    else:  # both
        sur_name_t = safe_get(row, col_sur_t)
        sur_name_p = safe_get(row, col_sur_p)
        ay_t = safe_get(row, col_tash)
        ay_p = safe_get(row, col_plain)
        print(f"[{sur_no}:{ay_no}] {sur_name_t} / {sur_name_p}")
        print(f"  بالتشكيل : {ay_t}")
        print(f"  بدون     : {ay_p}")

def main():
    if len(sys.argv) < 2:
        print("الاستخدام: python quran_root_search.py quran_corrected_global.csv")
        sys.exit(1)

    path = sys.argv[1]

    # اقرأ CSV
    try:
        df = pd.read_csv(path, dtype=str, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")

    # الأعمدة
    col_tash = DEFAULT_COL_TASHKEEL
    col_plain = DEFAULT_COL_PLAIN
    col_sur_t = DEFAULT_COL_SURAH_T
    col_sur_p = DEFAULT_COL_SURAH_P
    col_sur_no = DEFAULT_COL_SURAH_NO
    col_ayah_no = DEFAULT_COL_AYAH_NO

    # تحقق من وجود الأعمدة
    needed = [col_tash, col_plain, col_sur_t, col_sur_p, col_sur_no, col_ayah_no]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        print("أعمدة مفقودة في ملفك:", missing)
        print("عدّل أسماء الأعمدة في رأس السكربت لتطابق ملفك.")
        sys.exit(1)

    # هل يوجد عمود جذور؟
    col_roots = DEFAULT_COL_ROOTS
    has_roots = col_roots in df.columns if col_roots else False

    if has_roots:
        print(f"تم العثور على عمود جذور للآية: {col_roots} وسيُستخدم للبحث الجذري.")
    else:
        print("لا يوجد عمود جذور للآية في الملف؛ سيتم استخدام البحث النصي داخل الآية (ليس تحليلًا صرفيًا).")

    mode = choose_mode()

    # اختيار أسلوب المطابقة
    if has_roots:
        print("\nاختر أسلوب المطابقة:")
        print("1) مطابقة الجذر كجذر (باستخدام عمود الجذور)")
        print("2) مطابقة داخل نص الآية (بحث نصي)")
        while True:
            m = input("اختيارك (1/2): ").strip()
            if m == "1":
                match_mode = "roots"
                break
            if m == "2":
                match_mode = "text"
                break
            print("قيمة غير صحيحة.")
    else:
        match_mode = "text"

    print("\nاكتب الجذر للبحث (مثال: رحم) أو اكتب (exit) للخروج.\n")

    cols = (col_tash, col_plain, col_sur_t, col_sur_p, col_sur_no, col_ayah_no)

    while True:
        root = input("الجذر: ").strip()
        if not root:
            continue
        if root.lower() in ("exit", "quit", "q"):
            break

        matcher = build_matcher(root, match_mode)

        # تحديد النص الذي سيتم البحث فيه حسب أسلوب المطابقة
        if match_mode == "roots":
            mask = df[col_roots].apply(matcher)
        else:
            # نبحث في النص بدون تشكيل لتقليل مشاكل الهمزات/الحركات
            # ويمكن تغيير ذلك للبحث في col_tash إن رغبت
            mask = df[col_plain].apply(matcher)

        hits = df[mask]
        count = len(hits)

        print(f"\nعدد النتائج: {count}\n")
        if count == 0:
            continue

        for _, row in hits.iterrows():
            print_result(row, mode, cols)
        print("\n" + "-" * 60 + "\n")

if __name__ == "__main__":
    main()

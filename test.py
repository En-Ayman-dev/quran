import pandas as pd
from pathlib import Path

input_path = Path(r"Cl1.xlsx")
output_path = Path(r"Cl1_grouped_by_root.xlsx")

df = pd.read_excel(input_path)

# تنظيف أسماء الأعمدة
df.columns = (
    df.columns
    .astype(str)
    .str.strip()
    .str.replace("\u200f", "", regex=False)  # RTL mark
    .str.replace("\u200e", "", regex=False)  # LTR mark
)

print("الأعمدة بعد التنظيف:", list(df.columns))

# خرائط ذكية للأسماء العربية المحتملة
col_map = {}
for c in df.columns:
    if "كلم" in c:
        col_map["الكلمة"] = c
    if "جذر" in c:
        col_map["الجذر"] = c

if "الكلمة" not in col_map or "الجذر" not in col_map:
    raise ValueError(f"لم يتم العثور على أعمدة الكلمة/الجذر. الموجود: {df.columns}")

word_col = col_map["الكلمة"]
root_col = col_map["الجذر"]

# تنظيف القيم
df[word_col] = df[word_col].astype(str).str.strip()
df[root_col] = df[root_col].astype(str).str.strip()

# التجميع
out = (
    df.groupby([root_col, word_col], as_index=False)
      .size()
      .rename(columns={
          root_col: "الجذر",
          word_col: "الكلمة",
          "size": "عدد_ذكر_الكلمة"
      })
      .sort_values(["الجذر", "عدد_ذكر_الكلمة"], ascending=[True, False])
)

out.to_excel(output_path, index=False)

print("تم إنشاء الملف:", output_path)

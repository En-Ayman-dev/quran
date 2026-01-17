

# import csv
# import json
# import re
# from pathlib import Path
# from typing import Dict, List, Tuple, Optional

# import tkinter as tk
# from tkinter import filedialog, messagebox


# # -------------------- Helpers --------------------

# def read_root_ids(path: Path) -> List[int]:
#     text = path.read_text(encoding="utf-8", errors="ignore")
#     ids: List[int] = []
#     for line in text.splitlines():
#         line = line.strip()
#         if not line:
#             continue
#         m = re.search(r"\d+", line)
#         if not m:
#             continue
#         ids.append(int(m.group(0)))
#     return sorted(set(ids))


# def detect_delimiter(sample: str) -> str:
#     if "\t" in sample:
#         return "\t"
#     if sample.count(";") > sample.count(","):
#         return ";"
#     return ","


# def normalize_header(h: str) -> str:
#     return re.sub(r"\s+", "", (h or "").strip().lower())


# def find_header_index(headers: List[str], keys: List[str]) -> Optional[int]:
#     norm = [normalize_header(h) for h in headers]
#     keys_n = [normalize_header(k) for k in keys]
#     for k in keys_n:
#         for i, h in enumerate(norm):
#             if k == h or k in h:
#                 return i
#     return None


# def get_col(row: List[str], idx: Optional[int]) -> str:
#     if idx is None or idx < 0 or idx >= len(row):
#         return ""
#     return row[idx] or ""


# def md_escape(s: str) -> str:
#     return (s or "").replace("|", "\\|").replace("\r", "").strip()


# def html_escape(s: str) -> str:
#     s = s or ""
#     return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# def pick_text(row: List[str], idx_primary: Optional[int], idx_fallback: Optional[int]) -> str:
#     a = get_col(row, idx_primary).strip()
#     if a:
#         return a
#     return get_col(row, idx_fallback).strip()


# def chunk_list(xs: List[int], n: int) -> List[List[int]]:
#     return [xs[i:i+n] for i in range(0, len(xs), n)]


# def read_quran_rows(quran_path: Path, delim: Optional[str], encoding: str) -> Tuple[List[str], List[List[str]]]:
#     text = quran_path.read_text(encoding=encoding, errors="ignore")
#     lines = [ln for ln in text.splitlines() if ln.strip()]
#     if not lines:
#         raise ValueError("ملف القرآن فارغ.")
#     if delim is None:
#         delim = detect_delimiter(lines[0])

#     reader = csv.reader(lines, delimiter=delim)
#     try:
#         header = next(reader)
#     except StopIteration:
#         raise ValueError("ملف القرآن لا يحتوي بيانات.")
#     rows = [row for row in reader if row]
#     return header, rows


# # -------------------- Column mapping (FIXED for your schema) --------------------

# def has_quran_schema_v1(header: List[str]) -> bool:
#     """
#     يتحقق أن الهيدر مطابق تقريباً لما عرضته:
#     global_ayah, old_global, 1..13
#     """
#     norm = [h.strip() for h in header]
#     needed = ["global_ayah", "old_global", "1", "2", "3", "4", "10", "11", "12"]
#     return all(x in norm for x in needed)


# def build_maps(header: List[str], rows: List[List[str]]) -> dict:
#     """
#     ربط الأعمدة بطريقة ثابتة حسب نموذج ملفك لتجنب الأخطاء عند كثرة العربية في اسم السورة.
#     """
#     if not has_quran_schema_v1(header):
#         raise ValueError(
#             "ملف القرآن لا يطابق النموذج المتوقع.\n"
#             "المتوقع هيدر مثل: global_ayah,old_global,1,2,3,4,...,13\n"
#             "إذا ملفك مختلف، أعطني الهيدر كاملًا وسأضبطه."
#         )

#     # فهارس مباشرة بالأسماء
#     def idx(name: str) -> int:
#         return header.index(name)

#     gidx = idx("global_ayah")
#     old_idx = idx("old_global")

#     surah_num_idx = idx("1")
#     ayah_in_surah_idx = idx("2")

#     text_uthmani_idx = idx("3")   # نص عثماني
#     text_plain_idx = idx("4")     # نص مبسط

#     surah_name_uthmani_idx = idx("10")
#     surah_name_plain_idx = idx("11")

#     # optional columns
#     juz_idx = idx("12") if "12" in header else None

#     qmap: Dict[int, List[str]] = {}
#     bad = 0
#     for row in rows:
#         if gidx >= len(row):
#             bad += 1
#             continue
#         m = re.search(r"\d+", (row[gidx] or "").strip().lstrip("\ufeff"))
#         if not m:
#             bad += 1
#             continue
#         gid = int(m.group(0))
#         if gid not in qmap:
#             qmap[gid] = row

#     return {
#         "gidx": gidx,
#         "old_idx": old_idx,

#         # "surah_idx" هنا رقم السورة (1..114)
#         "surah_idx": surah_num_idx,

#         # "ain_idx" رقم الآية داخل السورة
#         "ain_idx": ayah_in_surah_idx,

#         # نص الآية: primary = عثماني (3)، fallback = مبسط (4)
#         "text_idx": text_uthmani_idx,
#         "plain_idx": text_plain_idx,

#         # أسماء السورة
#         "surah_name_uthmani_idx": surah_name_uthmani_idx,
#         "surah_name_plain_idx": surah_name_plain_idx,

#         "juz_idx": juz_idx,

#         "qmap": qmap,
#         "bad": bad
#     }


# # -------------------- Matching & context --------------------

# def match_root_to_quran(root_ids: List[int], qmap: Dict[int, List[str]]) -> Tuple[List[Tuple[int, List[str]]], List[int]]:
#     matched: List[Tuple[int, List[str]]] = []
#     missing: List[int] = []
#     for gid in root_ids:
#         row = qmap.get(gid)
#         if row is None:
#             missing.append(gid)
#         else:
#             matched.append((gid, row))
#     return matched, missing


# def get_context_ids(center_gid: int, prev_n: int, next_n: int) -> List[int]:
#     prev_n = max(0, int(prev_n))
#     next_n = max(0, int(next_n))
#     return list(range(center_gid - prev_n, center_gid)) + [center_gid] + list(range(center_gid + 1, center_gid + 1 + next_n))


# def filter_header_and_row(header: List[str], row: List[str], excluded: set) -> Tuple[List[str], List[str]]:
#     new_h, new_r = [], []
#     for i, h in enumerate(header):
#         if h in excluded:
#             continue
#         new_h.append(h)
#         new_r.append(row[i] if i < len(row) else "")
#     return new_h, new_r


# def discover_quran_file(root_file: Optional[Path] = None) -> Optional[Path]:
#     target_names = ["quran_corrected_global.csv", "quran_corrected_global.tsv"]
#     candidates: List[Path] = [Path(__file__).resolve().parent]

#     if root_file is not None:
#         candidates += [root_file.resolve().parent, root_file.resolve().parent.parent]

#     candidates.append(Path.cwd())

#     for base in candidates:
#         for name in target_names:
#             p = base / name
#             if p.exists() and p.is_file():
#                 return p

#     for base in candidates:
#         try:
#             for p in base.glob("quran_corrected_global.*"):
#                 if p.is_file():
#                     return p
#         except Exception:
#             pass

#     return None


# # -------------------- Writers --------------------

# def write_markdown_readable(
#     out_path: Path,
#     root_title: str,
#     quran_file: str,
#     header: List[str],
#     indices: dict,
#     root_ids: List[int],
#     matched: List[Tuple[int, List[str]]],
#     missing: List[int],
#     show_fields: List[str],
#     include_full_details: bool,
#     excluded_cols: set,
#     include_context: bool,
#     prev_n: int,
#     next_n: int,
#     qmap: Dict[int, List[str]]
# ) -> None:
#     f_header = [h for h in header if h not in excluded_cols]
#     show_fields = [f for f in show_fields if f in f_header]
#     orig_hmap = {h: i for i, h in enumerate(header)}

#     surah_num_idx = indices["surah_idx"]
#     ayah_in_surah_idx = indices["ain_idx"]
#     old_idx = indices["old_idx"]

#     text_idx = indices["text_idx"]
#     plain_idx = indices["plain_idx"]

#     sname_u_idx = indices["surah_name_uthmani_idx"]
#     sname_p_idx = indices["surah_name_plain_idx"]

#     md: List[str] = []
#     md.append(f"# آيات الجذر: {md_escape(root_title)}\n")

#     md.append("## الملخص")
#     md.append(f"- ملف القرآن: `{md_escape(quran_file)}`")
#     md.append(f"- أرقام ملف الجذر (Unique): **{len(root_ids)}**")
#     md.append(f"- مطابقات: **{len(matched)}**")
#     md.append(f"- غير موجودة: **{len(missing)}**")
#     md.append(f"- أعمدة مستبعدة من المخرجات: **{len(excluded_cols)}**")
#     if include_context:
#         md.append(f"- السياق: **{prev_n} قبل** + **{next_n} بعد**")
#     md.append("\n---\n")

#     md.append("## فهرس الآيات")
#     md.append("> اضغط على رقم الآية العامة للانتقال.\n")
#     for gid, row in matched:
#         surah_num = get_col(row, surah_num_idx).strip()
#         ain = get_col(row, ayah_in_surah_idx).strip()
#         sname = pick_text(row, sname_u_idx, sname_p_idx).strip()
#         label = f"{gid}"
#         if surah_num or ain:
#             label += f" (س{surah_num or '?'}:{ain or '?'})"
#         if sname:
#             label += f" — {sname}"
#         md.append(f"- [{md_escape(label)}](#g{gid})")
#     md.append("\n---\n")

#     md.append("## الآيات\n")

#     for gid, row in matched:
#         surah_num = get_col(row, surah_num_idx).strip()
#         ain = get_col(row, ayah_in_surah_idx).strip()
#         oldg = get_col(row, old_idx).strip()
#         sname = pick_text(row, sname_u_idx, sname_p_idx).strip()

#         # نص الآية الصحيح: 3 (عثماني) ثم 4 (مبسّط)
#         ayah_text = pick_text(row, text_idx, plain_idx).replace("\n", " ").strip()

#         md.append(f"### G{gid}")
#         md.append(f"<a id='g{gid}'></a>\n")

#         if include_context:
#             ids = get_context_ids(gid, prev_n, next_n)
#             md.append("**السياق (قبل/الآية/بعد):**\n")
#             for cid in ids:
#                 crow = qmap.get(cid)
#                 if crow is None:
#                     continue
#                 ctext = pick_text(crow, text_idx, plain_idx).replace("\n", " ").strip()
#                 prefix = "→" if cid == gid else "•"
#                 md.append(f"{prefix} **G{cid}**: {md_escape(ctext)}")
#             md.append("")

#         md.append("**الآية المطابقة:**")
#         md.append(f"> {md_escape(ayah_text)}\n")

#         info_bits = []
#         if sname:
#             info_bits.append(f"اسم السورة: **{md_escape(sname)}**")
#         if surah_num:
#             info_bits.append(f"رقم السورة: **{md_escape(surah_num)}**")
#         if ain:
#             info_bits.append(f"آية داخل السورة: **{md_escape(ain)}**")
#         info_bits.append(f"الرقم العام: **{gid}**")
#         if oldg:
#             info_bits.append(f"الترقيم القديم: **{md_escape(oldg)}**")

#         extra_bits = []
#         for field in show_fields:
#             if field in orig_hmap:
#                 val = get_col(row, orig_hmap[field]).strip()
#                 if val:
#                     extra_bits.append(f"{md_escape(field)}: **{md_escape(val)}**")

#         md.append("**المعلومات:**")
#         if info_bits:
#             md.append("- " + " | ".join(info_bits))
#         if extra_bits:
#             md.append("- " + " | ".join(extra_bits))
#         md.append("")

#         if include_full_details:
#             md.append("<details>")
#             md.append("<summary>عرض الأعمدة غير المستبعدة (تفاصيل)</summary>\n")
#             md.append("<ul>")
#             f_h, f_r = filter_header_and_row(header, row, excluded_cols)
#             for h, v in zip(f_h, f_r):
#                 md.append(f"<li><b>{html_escape(h)}</b>: {html_escape(v)}</li>")
#             md.append("</ul>")
#             md.append("</details>\n")

#         md.append("---\n")

#     if missing:
#         md.append("## أرقام غير موجودة في ملف القرآن\n")
#         for ch in chunk_list(missing, 60):
#             md.append(", ".join(str(x) for x in ch))
#         md.append("")

#     out_path.write_text("\n".join(md), encoding="utf-8")


# def write_json(
#     out_path: Path,
#     root_title: str,
#     quran_file: str,
#     header: List[str],
#     indices: dict,
#     root_ids: List[int],
#     matched: List[Tuple[int, List[str]]],
#     missing: List[int],
#     include_all_fields: bool,
#     include_fields: List[str],
#     excluded_cols: set,
#     include_context: bool,
#     prev_n: int,
#     next_n: int,
#     qmap: Dict[int, List[str]]
# ) -> None:
#     orig_hmap = {h: i for i, h in enumerate(header)}
#     include_fields = [f for f in include_fields if f not in excluded_cols]

#     surah_num_idx = indices["surah_idx"]
#     ayah_in_surah_idx = indices["ain_idx"]
#     old_idx = indices["old_idx"]
#     text_idx = indices["text_idx"]
#     plain_idx = indices["plain_idx"]
#     sname_u_idx = indices["surah_name_uthmani_idx"]
#     sname_p_idx = indices["surah_name_plain_idx"]

#     def row_to_obj(gid: int, row: List[str]) -> dict:
#         obj = {
#             "global_ayah": gid,
#             "old_global": get_col(row, old_idx).strip(),
#             "surah_number": get_col(row, surah_num_idx).strip(),
#             "ayah_in_surah": get_col(row, ayah_in_surah_idx).strip(),
#             "surah_name": pick_text(row, sname_u_idx, sname_p_idx).strip(),
#             "text": pick_text(row, text_idx, plain_idx).replace("\n", " ").strip(),
#         }

#         if include_context:
#             ids = get_context_ids(gid, prev_n, next_n)
#             ctx = []
#             for cid in ids:
#                 crow = qmap.get(cid)
#                 if crow is None:
#                     continue
#                 ctx.append({
#                     "global_ayah": cid,
#                     "text": pick_text(crow, text_idx, plain_idx).replace("\n", " ").strip()
#                 })
#             obj["context"] = ctx

#         if include_all_fields:
#             f_h, f_r = filter_header_and_row(header, row, excluded_cols)
#             obj["fields"] = {f_h[i]: (f_r[i] if i < len(f_r) else "") for i in range(len(f_h))}
#         else:
#             obj["fields"] = {}
#             for f in include_fields:
#                 if f in orig_hmap:
#                     obj["fields"][f] = get_col(row, orig_hmap[f])

#         return obj

#     data = {
#         "root": root_title,
#         "quran_file": quran_file,
#         "root_ids_count": len(root_ids),
#         "matched_count": len(matched),
#         "missing_count": len(missing),
#         "missing_ids": missing,
#         "excluded_columns": sorted(list(excluded_cols)),
#         "context": {"enabled": include_context, "prev": prev_n, "next": next_n},
#         "detected_schema": "quran_schema_v1 (global_ayah, old_global, 1..13)",
#         "fixed_columns": {
#             "global_ayah": "global_ayah",
#             "old_global": "old_global",
#             "surah_number": "1",
#             "ayah_in_surah": "2",
#             "text_uthmani": "3",
#             "text_plain": "4",
#             "surah_name_uthmani": "10",
#             "surah_name_plain": "11",
#         },
#         "verses": [row_to_obj(gid, row) for gid, row in matched],
#     }
#     out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# def write_csv(
#     out_path: Path,
#     header: List[str],
#     indices: dict,
#     matched: List[Tuple[int, List[str]]],
#     include_fields: List[str],
#     excluded_cols: set,
#     include_context: bool,
#     prev_n: int,
#     next_n: int,
#     qmap: Dict[int, List[str]]
# ) -> None:
#     include_fields = [f for f in include_fields if f not in excluded_cols]
#     orig_hmap = {h: i for i, h in enumerate(header)}

#     text_idx = indices["text_idx"]
#     plain_idx = indices["plain_idx"]

#     with out_path.open("w", encoding="utf-8", newline="") as f:
#         w = csv.writer(f)
#         out_header = ["global_ayah", "text"]
#         if include_context:
#             out_header += ["context_prev_next"]
#         out_header += include_fields
#         w.writerow(out_header)

#         for gid, row in matched:
#             txt = pick_text(row, text_idx, plain_idx).replace("\n", " ").strip()

#             ctx_text = ""
#             if include_context:
#                 ids = get_context_ids(gid, prev_n, next_n)
#                 parts = []
#                 for cid in ids:
#                     crow = qmap.get(cid)
#                     if crow is None:
#                         continue
#                     ctext = pick_text(crow, text_idx, plain_idx).replace("\n", " ").strip()
#                     mark = ">>" if cid == gid else ""
#                     parts.append(f"{mark}G{cid}:{ctext}")
#                 ctx_text = " | ".join(parts)

#             values = []
#             for fld in include_fields:
#                 values.append(get_col(row, orig_hmap[fld]))

#             out_row = [gid, txt]
#             if include_context:
#                 out_row.append(ctx_text)
#             out_row += values
#             w.writerow(out_row)


# # -------------------- GUI --------------------

# class App(tk.Tk):
#     def __init__(self):
#         super().__init__()
#         self.title("استخراج آيات الجذر (MD/JSON/CSV) + استبعاد أعمدة + سياق (ثابت لملفك)")
#         self.geometry("1180x780")

#         self.root_path = tk.StringVar()
#         self.quran_path = tk.StringVar()
#         self.out_dir = tk.StringVar()
#         self.out_base = tk.StringVar()

#         self.encoding = tk.StringVar(value="utf-8")
#         self.delim = tk.StringVar(value="auto")

#         self.format_md = tk.BooleanVar(value=True)
#         self.format_json = tk.BooleanVar(value=False)
#         self.format_csv = tk.BooleanVar(value=False)

#         self.include_full_details_md = tk.BooleanVar(value=True)
#         self.json_include_all_fields = tk.BooleanVar(value=False)

#         self.include_context = tk.BooleanVar(value=False)
#         self.prev_n = tk.StringVar(value="3")
#         self.next_n = tk.StringVar(value="3")

#         self.header_cache: List[str] = []
#         self.indices_cache: Optional[dict] = None

#         self.excluded_cols = set()
#         self.excluded_listbox = None
#         self.columns_listbox = None
#         self.status = None

#         self._build_ui()

#         auto_q = discover_quran_file()
#         if auto_q:
#             self.quran_path.set(str(auto_q))

#         self._toggle_context_inputs()

#     def _build_ui(self):
#         pad = {"padx": 10, "pady": 6}

#         tk.Label(self, text="1) ملف الجذر:").grid(row=0, column=0, sticky="w", **pad)
#         tk.Entry(self, textvariable=self.root_path, width=100).grid(row=0, column=1, sticky="we", **pad)
#         tk.Button(self, text="اختيار...", command=self.pick_root).grid(row=0, column=2, **pad)

#         tk.Label(self, text="2) ملف القرآن المصحح (تلقائي):").grid(row=1, column=0, sticky="w", **pad)
#         tk.Entry(self, textvariable=self.quran_path, width=100).grid(row=1, column=1, sticky="we", **pad)
#         tk.Button(self, text="تغيير/اختيار...", command=self.pick_quran).grid(row=1, column=2, **pad)

#         tk.Label(self, text="3) مجلد حفظ المخرجات:").grid(row=2, column=0, sticky="w", **pad)
#         tk.Entry(self, textvariable=self.out_dir, width=100).grid(row=2, column=1, sticky="we", **pad)
#         tk.Button(self, text="اختيار...", command=self.pick_out_dir).grid(row=2, column=2, **pad)

#         tk.Label(self, text="4) اسم المخرجات (Base name):").grid(row=3, column=0, sticky="w", **pad)
#         tk.Entry(self, textvariable=self.out_base, width=100).grid(row=3, column=1, sticky="we", **pad)
#         tk.Button(self, text="تلقائي", command=self.set_base_from_root).grid(row=3, column=2, **pad)

#         opts = tk.LabelFrame(self, text="الإعدادات")
#         opts.grid(row=4, column=0, columnspan=3, sticky="we", padx=10, pady=8)

#         tk.Label(opts, text="Encoding:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
#         tk.Entry(opts, textvariable=self.encoding, width=14).grid(row=0, column=1, sticky="w", padx=8, pady=6)

#         tk.Label(opts, text="Delimiter:").grid(row=0, column=2, sticky="w", padx=8, pady=6)
#         tk.OptionMenu(opts, self.delim, "auto", "comma (,)", "tab (\\t)", "semicolon (;)").grid(row=0, column=3, sticky="w", padx=8, pady=6)

#         tk.Label(opts, text="تنسيقات الحفظ:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
#         tk.Checkbutton(opts, text="Markdown (.md)", variable=self.format_md).grid(row=1, column=1, sticky="w", padx=8, pady=6)
#         tk.Checkbutton(opts, text="JSON (.json)", variable=self.format_json).grid(row=1, column=2, sticky="w", padx=8, pady=6)
#         tk.Checkbutton(opts, text="CSV (.csv)", variable=self.format_csv).grid(row=1, column=3, sticky="w", padx=8, pady=6)

#         tk.Checkbutton(opts, text="Markdown: تفاصيل قابلة للطي", variable=self.include_full_details_md).grid(
#             row=2, column=0, columnspan=2, sticky="w", padx=8, pady=6
#         )
#         tk.Checkbutton(opts, text="JSON: تضمين كل الأعمدة (بعد الاستبعاد)", variable=self.json_include_all_fields).grid(
#             row=2, column=2, columnspan=2, sticky="w", padx=8, pady=6
#         )

#         tk.Checkbutton(
#             opts,
#             text="جلب الآيات السابقة واللاحقة (سياق)",
#             variable=self.include_context,
#             command=self._toggle_context_inputs
#         ).grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=6)

#         self.prev_label = tk.Label(opts, text="عدد السابقة:")
#         self.prev_entry = tk.Entry(opts, textvariable=self.prev_n, width=8)
#         self.next_label = tk.Label(opts, text="عدد اللاحقة:")
#         self.next_entry = tk.Entry(opts, textvariable=self.next_n, width=8)

#         self.prev_label.grid(row=3, column=2, sticky="e", padx=6, pady=6)
#         self.prev_entry.grid(row=3, column=3, sticky="w", padx=6, pady=6)
#         self.next_label.grid(row=3, column=4, sticky="e", padx=6, pady=6)
#         self.next_entry.grid(row=3, column=5, sticky="w", padx=6, pady=6)

#         cols = tk.LabelFrame(self, text="إدارة الأعمدة (اختيار + استبعاد نهائي)")
#         cols.grid(row=5, column=0, columnspan=3, sticky="nsew", padx=10, pady=8)

#         tk.Button(cols, text="تحميل الأعمدة", command=self.load_columns).grid(row=0, column=0, sticky="w", padx=8, pady=6)
#         tk.Button(cols, text="اختيار افتراضي", command=self.select_default_columns).grid(row=0, column=1, sticky="w", padx=8, pady=6)
#         tk.Button(cols, text="مسح الاختيار", command=self.clear_column_selection).grid(row=0, column=2, sticky="w", padx=8, pady=6)

#         tk.Button(cols, text="حذف الأعمدة المحددة من المخرجات (نهائياً)", command=self.exclude_selected_columns).grid(
#             row=0, column=3, sticky="w", padx=8, pady=6
#         )
#         tk.Button(cols, text="استرجاع أعمدة مستبعدة", command=self.restore_excluded_columns).grid(
#             row=0, column=4, sticky="w", padx=8, pady=6
#         )

#         tk.Label(cols, text="الأعمدة المتاحة:").grid(row=1, column=0, sticky="w", padx=8)
#         tk.Label(cols, text="الأعمدة المستبعدة نهائياً:").grid(row=1, column=3, sticky="w", padx=8)

#         self.columns_listbox = tk.Listbox(cols, selectmode="extended", height=10, width=65)
#         self.columns_listbox.grid(row=2, column=0, columnspan=3, sticky="we", padx=8, pady=6)

#         self.excluded_listbox = tk.Listbox(cols, selectmode="extended", height=10, width=55)
#         self.excluded_listbox.grid(row=2, column=3, columnspan=2, sticky="we", padx=8, pady=6)

#         tk.Button(self, text="ابدأ (إنشاء المخرجات)", command=self.run, height=2).grid(
#             row=6, column=0, columnspan=3, padx=10, pady=10, sticky="we"
#         )

#         self.status = tk.Text(self, height=12, wrap="word")
#         self.status.grid(row=7, column=0, columnspan=3, padx=10, pady=8, sticky="nsew")
#         self.status.configure(state="disabled")

#         self.grid_columnconfigure(1, weight=1)
#         self.grid_rowconfigure(5, weight=1)
#         self.grid_rowconfigure(7, weight=1)

#     def _toggle_context_inputs(self):
#         enabled = bool(self.include_context.get())
#         state = "normal" if enabled else "disabled"
#         self.prev_entry.configure(state=state)
#         self.next_entry.configure(state=state)
#         self.prev_label.configure(state=state)
#         self.next_label.configure(state=state)

#         if not self.prev_n.get().strip():
#             self.prev_n.set("3")
#         if not self.next_n.get().strip():
#             self.next_n.set("3")

#     def log(self, msg: str):
#         self.status.configure(state="normal")
#         self.status.insert("end", msg + "\n")
#         self.status.see("end")
#         self.status.configure(state="disabled")

#     def _delim_value(self) -> Optional[str]:
#         v = self.delim.get()
#         if v == "auto":
#             return None
#         if v.startswith("comma"):
#             return ","
#         if v.startswith("tab"):
#             return "\t"
#         if v.startswith("semicolon"):
#             return ";"
#         return None

#     def set_base_from_root(self):
#         p = self.root_path.get().strip('" ')
#         if p:
#             self.out_base.set(Path(p).stem)

#     def pick_root(self):
#         p = filedialog.askopenfilename(title="اختر ملف الجذر", filetypes=[("All Files", "*.*")])
#         if not p:
#             return
#         self.root_path.set(p)
#         rp = Path(p)
#         if not self.out_dir.get().strip():
#             self.out_dir.set(str(rp.parent))
#         self.out_base.set(rp.stem)

#         auto_q = discover_quran_file(rp)
#         if auto_q and not self.quran_path.get().strip():
#             self.quran_path.set(str(auto_q))

#     def pick_quran(self):
#         p = filedialog.askopenfilename(
#             title="اختر ملف القرآن المصحح (global_ayah, old_global, 1..13)",
#             filetypes=[("CSV/TSV", "*.csv *.tsv *.txt"), ("All Files", "*.*")]
#         )
#         if p:
#             self.quran_path.set(p)

#     def pick_out_dir(self):
#         p = filedialog.askdirectory(title="اختر مجلد حفظ المخرجات")
#         if p:
#             self.out_dir.set(p)

#     def load_columns(self):
#         qpath = Path(self.quran_path.get().strip('" '))
#         if not qpath.exists():
#             messagebox.showerror("خطأ", "ملف القرآن غير موجود.")
#             return

#         try:
#             header, rows = read_quran_rows(qpath, self._delim_value(), self.encoding.get().strip() or "utf-8")
#             self.header_cache = header
#             self.indices_cache = build_maps(header, rows)
#         except Exception as e:
#             messagebox.showerror("خطأ", str(e))
#             return

#         # تنظيف الاستبعاد
#         self.excluded_cols = {h for h in self.excluded_cols if h in self.header_cache}
#         self.refresh_columns_ui()
#         self.log("تم تحميل الأعمدة وفق schema ثابت.")
#         idx = self.indices_cache
#         self.log(f"الربط: surah=1 ayah_in_surah=2 text=3 plain=4 surah_name=10/11")

#     def refresh_columns_ui(self):
#         available = [h for h in self.header_cache if h not in self.excluded_cols]
#         excluded = sorted(list(self.excluded_cols))

#         self.columns_listbox.delete(0, "end")
#         for h in available:
#             self.columns_listbox.insert("end", h)

#         self.excluded_listbox.delete(0, "end")
#         for h in excluded:
#             self.excluded_listbox.insert("end", h)

#     def select_default_columns(self):
#         if not self.header_cache:
#             self.load_columns()
#             if not self.header_cache:
#                 return

#         available = [h for h in self.header_cache if h not in self.excluded_cols]
#         want = set(["1", "2", "10", "11", "12", "old_global"])  # افتراضي مفيد
#         self.columns_listbox.selection_clear(0, tk.END)
#         for i, h in enumerate(available):
#             if h in want:
#                 self.columns_listbox.selection_set(i)

#     def clear_column_selection(self):
#         self.columns_listbox.focus_set()
#         self.columns_listbox.selection_clear(0, tk.END)
#         self.columns_listbox.update_idletasks()

#     def exclude_selected_columns(self):
#         if not self.header_cache:
#             messagebox.showerror("خطأ", "حمّل الأعمدة أولاً.")
#             return

#         available = [h for h in self.header_cache if h not in self.excluded_cols]
#         idxs = list(self.columns_listbox.curselection())
#         if not idxs:
#             messagebox.showinfo("تنبيه", "اختر أعمدة من القائمة المتاحة ثم اضغط حذف.")
#             return

#         to_exclude = {available[i] for i in idxs}

#         # منع استبعاد أعمدة أساسية تجعل البرنامج غير مفيد
#         protected = {"global_ayah", "3", "4"}  # نحتاج نص الآية دائماً
#         if any(c in protected for c in to_exclude):
#             messagebox.showerror("خطأ", "لا يمكن استبعاد: global_ayah أو 3 أو 4 لأنها أعمدة أساسية للنص/المطابقة.")
#             return

#         self.excluded_cols |= to_exclude
#         self.columns_listbox.selection_clear(0, tk.END)
#         self.refresh_columns_ui()
#         self.log(f"تم استبعاد {len(to_exclude)} عمود(أعمدة).")

#     def restore_excluded_columns(self):
#         idxs = list(self.excluded_listbox.curselection())
#         if not idxs:
#             messagebox.showinfo("تنبيه", "اختر أعمدة من قائمة المستبعدة لاسترجاعها.")
#             return

#         excluded_sorted = sorted(list(self.excluded_cols))
#         to_restore = {excluded_sorted[i] for i in idxs}
#         self.excluded_cols -= to_restore

#         self.excluded_listbox.selection_clear(0, tk.END)
#         self.refresh_columns_ui()
#         self.log(f"تم استرجاع {len(to_restore)} عمود(أعمدة).")

#     def _selected_columns(self) -> List[str]:
#         if not self.header_cache:
#             return []
#         available = [h for h in self.header_cache if h not in self.excluded_cols]
#         idxs = list(self.columns_listbox.curselection())
#         return [available[i] for i in idxs]

#     def _parse_context_numbers(self) -> Tuple[int, int]:
#         def parse_nonneg(s: str, name: str) -> int:
#             s = (s or "").strip()
#             if s == "":
#                 return 3
#             if not re.fullmatch(r"\d+", s):
#                 raise ValueError(f"{name} يجب أن يكون رقم صحيح (0 أو أكثر).")
#             return int(s)

#         prev_n = parse_nonneg(self.prev_n.get(), "عدد السابقة")
#         next_n = parse_nonneg(self.next_n.get(), "عدد اللاحقة")
#         return prev_n, next_n

#     def run(self):
#         self.status.configure(state="normal")
#         self.status.delete("1.0", "end")
#         self.status.configure(state="disabled")

#         root_file = Path(self.root_path.get().strip('" '))
#         quran_file = Path(self.quran_path.get().strip('" '))
#         out_dir = Path(self.out_dir.get().strip('" ')) if self.out_dir.get().strip() else root_file.parent
#         base = (self.out_base.get().strip() or root_file.stem)

#         if not root_file.exists():
#             messagebox.showerror("خطأ", "اختر ملف الجذر الصحيح.")
#             return

#         if not out_dir.exists():
#             out_dir.mkdir(parents=True, exist_ok=True)

#         if not quran_file.exists():
#             auto_q = discover_quran_file(root_file)
#             if auto_q:
#                 quran_file = auto_q
#                 self.quran_path.set(str(auto_q))
#             else:
#                 messagebox.showerror("خطأ", "لم يتم العثور تلقائياً على quran_corrected_global.csv. اختره يدوياً.")
#                 return

#         if not (self.format_md.get() or self.format_json.get() or self.format_csv.get()):
#             messagebox.showerror("خطأ", "اختر على الأقل تنسيق حفظ واحد.")
#             return

#         enc = self.encoding.get().strip() or "utf-8"
#         delim = self._delim_value()

#         include_ctx = bool(self.include_context.get())
#         prev_n, next_n = (3, 3)
#         try:
#             if include_ctx:
#                 prev_n, next_n = self._parse_context_numbers()
#         except Exception as e:
#             messagebox.showerror("خطأ", str(e))
#             return

#         try:
#             self.log("قراءة ملف الجذر...")
#             root_ids = read_root_ids(root_file)
#             if not root_ids:
#                 raise ValueError("ملف الجذر لا يحتوي أرقام قابلة للاستخراج.")

#             self.log("قراءة ملف القرآن...")
#             header, rows = read_quran_rows(quran_file, delim, enc)
#             indices = build_maps(header, rows)
#             qmap = indices["qmap"]

#             matched, missing = match_root_to_quran(root_ids, qmap)
#             if not matched:
#                 raise ValueError("لا توجد مطابقات. تأكد أن أرقام ملف الجذر تطابق global_ayah.")

#             self.header_cache = header
#             self.indices_cache = indices
#             self.excluded_cols = {h for h in self.excluded_cols if h in header}
#             self.refresh_columns_ui()

#             selected_cols = self._selected_columns()
#             outputs_made = []

#             if self.format_md.get():
#                 out_md = out_dir / f"{base}.md"
#                 write_markdown_readable(
#                     out_path=out_md,
#                     root_title=root_file.name,
#                     quran_file=quran_file.name,
#                     header=header,
#                     indices=indices,
#                     root_ids=root_ids,
#                     matched=matched,
#                     missing=missing,
#                     show_fields=selected_cols,
#                     include_full_details=bool(self.include_full_details_md.get()),
#                     excluded_cols=self.excluded_cols,
#                     include_context=include_ctx,
#                     prev_n=prev_n,
#                     next_n=next_n,
#                     qmap=qmap
#                 )
#                 outputs_made.append(out_md)

#             if self.format_json.get():
#                 out_json = out_dir / f"{base}.json"
#                 write_json(
#                     out_path=out_json,
#                     root_title=root_file.name,
#                     quran_file=quran_file.name,
#                     header=header,
#                     indices=indices,
#                     root_ids=root_ids,
#                     matched=matched,
#                     missing=missing,
#                     include_all_fields=bool(self.json_include_all_fields.get()),
#                     include_fields=selected_cols,
#                     excluded_cols=self.excluded_cols,
#                     include_context=include_ctx,
#                     prev_n=prev_n,
#                     next_n=next_n,
#                     qmap=qmap
#                 )
#                 outputs_made.append(out_json)

#             if self.format_csv.get():
#                 out_csv = out_dir / f"{base}.csv"
#                 write_csv(
#                     out_path=out_csv,
#                     header=header,
#                     indices=indices,
#                     matched=matched,
#                     include_fields=selected_cols,
#                     excluded_cols=self.excluded_cols,
#                     include_context=include_ctx,
#                     prev_n=prev_n,
#                     next_n=next_n,
#                     qmap=qmap
#                 )
#                 outputs_made.append(out_csv)

#             self.log("تم بنجاح.")
#             self.log(f"- Base name: {base}")
#             self.log(f"- مطابقات: {len(matched)}")
#             self.log(f"- غير موجودة: {len(missing)}")
#             if include_ctx:
#                 self.log(f"- السياق: {prev_n} قبل + {next_n} بعد")
#             self.log(f"- المخرجات:")
#             for p in outputs_made:
#                 self.log(f"  * {p}")

#             messagebox.showinfo("تم", "تم إنشاء الملفات:\n" + "\n".join(str(p) for p in outputs_made))

#         except Exception as e:
#             messagebox.showerror("فشل", str(e))
#             self.log(f"خطأ: {e}")


# if __name__ == "__main__":
#     App().mainloop()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import tkinter as tk
from tkinter import filedialog, messagebox


# -------------------- Default folders (NEW) --------------------

DEFAULT_ROOT_DIR = Path(r"F:\Quran\Q\QQ\Root")
DEFAULT_OUTPUT_BASE_DIR = Path(r"F:\Quran\Q\QQ\OutPut")


# -------------------- Helpers --------------------

def read_root_ids(path: Path) -> List[int]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    ids: List[int] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.search(r"\d+", line)
        if not m:
            continue
        ids.append(int(m.group(0)))
    return sorted(set(ids))


def detect_delimiter(sample: str) -> str:
    if "\t" in sample:
        return "\t"
    if sample.count(";") > sample.count(","):
        return ";"
    return ","


def normalize_header(h: str) -> str:
    return re.sub(r"\s+", "", (h or "").strip().lower())


def find_header_index(headers: List[str], keys: List[str]) -> Optional[int]:
    norm = [normalize_header(h) for h in headers]
    keys_n = [normalize_header(k) for k in keys]
    for k in keys_n:
        for i, h in enumerate(norm):
            if k == h or k in h:
                return i
    return None


def get_col(row: List[str], idx: Optional[int]) -> str:
    if idx is None or idx < 0 or idx >= len(row):
        return ""
    return row[idx] or ""


def md_escape(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\r", "").strip()


def html_escape(s: str) -> str:
    s = s or ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pick_text(row: List[str], idx_primary: Optional[int], idx_fallback: Optional[int]) -> str:
    a = get_col(row, idx_primary).strip()
    if a:
        return a
    return get_col(row, idx_fallback).strip()


def chunk_list(xs: List[int], n: int) -> List[List[int]]:
    return [xs[i:i+n] for i in range(0, len(xs), n)]


def read_quran_rows(quran_path: Path, delim: Optional[str], encoding: str) -> Tuple[List[str], List[List[str]]]:
    text = quran_path.read_text(encoding=encoding, errors="ignore")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise ValueError("ملف القرآن فارغ.")
    if delim is None:
        delim = detect_delimiter(lines[0])

    reader = csv.reader(lines, delimiter=delim)
    try:
        header = next(reader)
    except StopIteration:
        raise ValueError("ملف القرآن لا يحتوي بيانات.")
    rows = [row for row in reader if row]
    return header, rows


# -------------------- Column mapping (fixed for your schema) --------------------

def has_quran_schema_v1(header: List[str]) -> bool:
    norm = [h.strip() for h in header]
    needed = ["global_ayah", "old_global", "1", "2", "3", "4", "10", "11", "12"]
    return all(x in norm for x in needed)


def build_maps(header: List[str], rows: List[List[str]]) -> dict:
    if not has_quran_schema_v1(header):
        raise ValueError(
            "ملف القرآن لا يطابق النموذج المتوقع.\n"
            "المتوقع هيدر مثل: global_ayah,old_global,1,2,3,4,...,13"
        )

    def idx(name: str) -> int:
        return header.index(name)

    gidx = idx("global_ayah")
    old_idx = idx("old_global")

    surah_num_idx = idx("1")
    ayah_in_surah_idx = idx("2")

    text_uthmani_idx = idx("3")
    text_plain_idx = idx("4")

    surah_name_uthmani_idx = idx("10")
    surah_name_plain_idx = idx("11")

    juz_idx = idx("12") if "12" in header else None

    qmap: Dict[int, List[str]] = {}
    bad = 0
    for row in rows:
        if gidx >= len(row):
            bad += 1
            continue
        m = re.search(r"\d+", (row[gidx] or "").strip().lstrip("\ufeff"))
        if not m:
            bad += 1
            continue
        gid = int(m.group(0))
        if gid not in qmap:
            qmap[gid] = row

    return {
        "gidx": gidx,
        "old_idx": old_idx,
        "surah_idx": surah_num_idx,
        "ain_idx": ayah_in_surah_idx,
        "text_idx": text_uthmani_idx,
        "plain_idx": text_plain_idx,
        "surah_name_uthmani_idx": surah_name_uthmani_idx,
        "surah_name_plain_idx": surah_name_plain_idx,
        "juz_idx": juz_idx,
        "qmap": qmap,
        "bad": bad
    }


# -------------------- Matching & context --------------------

def match_root_to_quran(root_ids: List[int], qmap: Dict[int, List[str]]) -> Tuple[List[Tuple[int, List[str]]], List[int]]:
    matched: List[Tuple[int, List[str]]] = []
    missing: List[int] = []
    for gid in root_ids:
        row = qmap.get(gid)
        if row is None:
            missing.append(gid)
        else:
            matched.append((gid, row))
    return matched, missing


def get_context_ids(center_gid: int, prev_n: int, next_n: int) -> List[int]:
    prev_n = max(0, int(prev_n))
    next_n = max(0, int(next_n))
    return list(range(center_gid - prev_n, center_gid)) + [center_gid] + list(range(center_gid + 1, center_gid + 1 + next_n))


def filter_header_and_row(header: List[str], row: List[str], excluded: set) -> Tuple[List[str], List[str]]:
    new_h, new_r = [], []
    for i, h in enumerate(header):
        if h in excluded:
            continue
        new_h.append(h)
        new_r.append(row[i] if i < len(row) else "")
    return new_h, new_r


def discover_quran_file(root_file: Optional[Path] = None) -> Optional[Path]:
    target_names = ["quran_corrected_global.csv", "quran_corrected_global.tsv"]
    candidates: List[Path] = []

    # prefer your project layout
    candidates.append(Path(r"F:\Quran\Q\QQ"))
    candidates.append(Path(__file__).resolve().parent)
    if root_file is not None:
        candidates += [root_file.resolve().parent, root_file.resolve().parent.parent]
    candidates.append(Path.cwd())

    for base in candidates:
        for name in target_names:
            p = base / name
            if p.exists() and p.is_file():
                return p
    for base in candidates:
        try:
            for p in base.glob("quran_corrected_global.*"):
                if p.is_file():
                    return p
        except Exception:
            pass
    return None


# -------------------- Writers --------------------

def write_markdown_readable(
    out_path: Path,
    root_title: str,
    quran_file: str,
    header: List[str],
    indices: dict,
    root_ids: List[int],
    matched: List[Tuple[int, List[str]]],
    missing: List[int],
    show_fields: List[str],
    include_full_details: bool,
    excluded_cols: set,
    include_context: bool,
    prev_n: int,
    next_n: int,
    qmap: Dict[int, List[str]]
) -> None:
    f_header = [h for h in header if h not in excluded_cols]
    show_fields = [f for f in show_fields if f in f_header]
    orig_hmap = {h: i for i, h in enumerate(header)}

    surah_num_idx = indices["surah_idx"]
    ayah_in_surah_idx = indices["ain_idx"]
    old_idx = indices["old_idx"]

    text_idx = indices["text_idx"]
    plain_idx = indices["plain_idx"]

    sname_u_idx = indices["surah_name_uthmani_idx"]
    sname_p_idx = indices["surah_name_plain_idx"]

    md: List[str] = []
    md.append(f"# آيات الجذر: {md_escape(root_title)}\n")

    md.append("## الملخص")
    md.append(f"- ملف القرآن: `{md_escape(quran_file)}`")
    md.append(f"- أرقام ملف الجذر (Unique): **{len(root_ids)}**")
    md.append(f"- مطابقات: **{len(matched)}**")
    md.append(f"- غير موجودة: **{len(missing)}**")
    if include_context:
        md.append(f"- السياق: **{prev_n} قبل** + **{next_n} بعد**")
    md.append("\n---\n")

    md.append("## فهرس الآيات")
    md.append("> اضغط على رقم الآية العامة للانتقال.\n")
    for gid, row in matched:
        surah_num = get_col(row, surah_num_idx).strip()
        ain = get_col(row, ayah_in_surah_idx).strip()
        sname = pick_text(row, sname_u_idx, sname_p_idx).strip()
        label = f"{gid} (س{surah_num or '?'}:{ain or '?'})"
        if sname:
            label += f" — {sname}"
        md.append(f"- [{md_escape(label)}](#g{gid})")
    md.append("\n---\n")

    md.append("## الآيات\n")

    for gid, row in matched:
        surah_num = get_col(row, surah_num_idx).strip()
        ain = get_col(row, ayah_in_surah_idx).strip()
        oldg = get_col(row, old_idx).strip()
        sname = pick_text(row, sname_u_idx, sname_p_idx).strip()

        ayah_text = pick_text(row, text_idx, plain_idx).replace("\n", " ").strip()

        md.append(f"### G{gid}")
        md.append(f"<a id='g{gid}'></a>\n")

        if include_context:
            ids = get_context_ids(gid, prev_n, next_n)
            md.append("**السياق (قبل/الآية/بعد):**\n")
            for cid in ids:
                crow = qmap.get(cid)
                if crow is None:
                    continue
                ctext = pick_text(crow, text_idx, plain_idx).replace("\n", " ").strip()
                prefix = "→" if cid == gid else "•"
                md.append(f"{prefix} **G{cid}**: {md_escape(ctext)}")
            md.append("")

        md.append("**الآية المطابقة:**")
        md.append(f"> {md_escape(ayah_text)}\n")

        info_bits = []
        if sname:
            info_bits.append(f"اسم السورة: **{md_escape(sname)}**")
        info_bits.append(f"رقم السورة: **{md_escape(surah_num)}**")
        info_bits.append(f"آية داخل السورة: **{md_escape(ain)}**")
        info_bits.append(f"الرقم العام: **{gid}**")
        if oldg:
            info_bits.append(f"الترقيم القديم: **{md_escape(oldg)}**")

        extra_bits = []
        for field in show_fields:
            val = get_col(row, orig_hmap[field]).strip() if field in orig_hmap else ""
            if val:
                extra_bits.append(f"{md_escape(field)}: **{md_escape(val)}**")

        md.append("**المعلومات:**")
        md.append("- " + " | ".join(info_bits))
        if extra_bits:
            md.append("- " + " | ".join(extra_bits))
        md.append("")

        if include_full_details:
            md.append("<details>")
            md.append("<summary>عرض الأعمدة غير المستبعدة (تفاصيل)</summary>\n")
            md.append("<ul>")
            f_h, f_r = filter_header_and_row(header, row, excluded_cols)
            for h, v in zip(f_h, f_r):
                md.append(f"<li><b>{html_escape(h)}</b>: {html_escape(v)}</li>")
            md.append("</ul>")
            md.append("</details>\n")

        md.append("---\n")

    if missing:
        md.append("## أرقام غير موجودة في ملف القرآن\n")
        for ch in chunk_list(missing, 60):
            md.append(", ".join(str(x) for x in ch))
        md.append("")

    out_path.write_text("\n".join(md), encoding="utf-8")


def write_json(
    out_path: Path,
    root_title: str,
    quran_file: str,
    header: List[str],
    indices: dict,
    root_ids: List[int],
    matched: List[Tuple[int, List[str]]],
    missing: List[int],
    include_all_fields: bool,
    include_fields: List[str],
    excluded_cols: set,
    include_context: bool,
    prev_n: int,
    next_n: int,
    qmap: Dict[int, List[str]]
) -> None:
    orig_hmap = {h: i for i, h in enumerate(header)}
    include_fields = [f for f in include_fields if f not in excluded_cols]

    surah_num_idx = indices["surah_idx"]
    ayah_in_surah_idx = indices["ain_idx"]
    old_idx = indices["old_idx"]
    text_idx = indices["text_idx"]
    plain_idx = indices["plain_idx"]
    sname_u_idx = indices["surah_name_uthmani_idx"]
    sname_p_idx = indices["surah_name_plain_idx"]

    def row_to_obj(gid: int, row: List[str]) -> dict:
        obj = {
            "global_ayah": gid,
            "old_global": get_col(row, old_idx).strip(),
            "surah_number": get_col(row, surah_num_idx).strip(),
            "ayah_in_surah": get_col(row, ayah_in_surah_idx).strip(),
            "surah_name": pick_text(row, sname_u_idx, sname_p_idx).strip(),
            "text": pick_text(row, text_idx, plain_idx).replace("\n", " ").strip(),
        }

        if include_context:
            ids = get_context_ids(gid, prev_n, next_n)
            obj["context"] = [
                {"global_ayah": cid, "text": pick_text(qmap[cid], text_idx, plain_idx).replace("\n", " ").strip()}
                for cid in ids if cid in qmap
            ]

        if include_all_fields:
            f_h, f_r = filter_header_and_row(header, row, excluded_cols)
            obj["fields"] = {f_h[i]: (f_r[i] if i < len(f_r) else "") for i in range(len(f_h))}
        else:
            obj["fields"] = {f: get_col(row, orig_hmap[f]) for f in include_fields if f in orig_hmap}

        return obj

    data = {
        "root": root_title,
        "quran_file": quran_file,
        "root_ids_count": len(root_ids),
        "matched_count": len(matched),
        "missing_count": len(missing),
        "missing_ids": missing,
        "excluded_columns": sorted(list(excluded_cols)),
        "context": {"enabled": include_context, "prev": prev_n, "next": next_n},
        "verses": [row_to_obj(gid, row) for gid, row in matched],
    }
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(
    out_path: Path,
    header: List[str],
    indices: dict,
    matched: List[Tuple[int, List[str]]],
    include_fields: List[str],
    excluded_cols: set,
    include_context: bool,
    prev_n: int,
    next_n: int,
    qmap: Dict[int, List[str]]
) -> None:
    include_fields = [f for f in include_fields if f not in excluded_cols]
    orig_hmap = {h: i for i, h in enumerate(header)}

    text_idx = indices["text_idx"]
    plain_idx = indices["plain_idx"]

    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        out_header = ["global_ayah", "text"]
        if include_context:
            out_header += ["context_prev_next"]
        out_header += include_fields
        w.writerow(out_header)

        for gid, row in matched:
            txt = pick_text(row, text_idx, plain_idx).replace("\n", " ").strip()

            ctx_text = ""
            if include_context:
                ids = get_context_ids(gid, prev_n, next_n)
                parts = []
                for cid in ids:
                    if cid not in qmap:
                        continue
                    ctext = pick_text(qmap[cid], text_idx, plain_idx).replace("\n", " ").strip()
                    mark = ">>" if cid == gid else ""
                    parts.append(f"{mark}G{cid}:{ctext}")
                ctx_text = " | ".join(parts)

            values = [get_col(row, orig_hmap[fld]) for fld in include_fields if fld in orig_hmap]

            out_row = [gid, txt]
            if include_context:
                out_row.append(ctx_text)
            out_row += values
            w.writerow(out_row)


# -------------------- GUI --------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("استخراج آيات الجذر (مسارات افتراضية ثابتة + مجلد لكل جذر)")
        self.geometry("1180x780")

        self.root_path = tk.StringVar()
        self.quran_path = tk.StringVar()
        self.out_dir = tk.StringVar()
        self.out_base = tk.StringVar()

        self.encoding = tk.StringVar(value="utf-8")
        self.delim = tk.StringVar(value="auto")

        self.format_md = tk.BooleanVar(value=True)
        self.format_json = tk.BooleanVar(value=False)
        self.format_csv = tk.BooleanVar(value=False)

        self.include_full_details_md = tk.BooleanVar(value=True)
        self.json_include_all_fields = tk.BooleanVar(value=False)

        self.include_context = tk.BooleanVar(value=False)
        self.prev_n = tk.StringVar(value="3")
        self.next_n = tk.StringVar(value="3")

        self.header_cache: List[str] = []
        self.indices_cache: Optional[dict] = None

        self.excluded_cols = set()
        self.excluded_listbox = None
        self.columns_listbox = None
        self.status = None

        self._build_ui()

        # default output base dir
        if DEFAULT_OUTPUT_BASE_DIR.exists():
            self.out_dir.set(str(DEFAULT_OUTPUT_BASE_DIR))

        auto_q = discover_quran_file()
        if auto_q:
            self.quran_path.set(str(auto_q))

        self._toggle_context_inputs()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        tk.Label(self, text="1) ملف الجذر:").grid(row=0, column=0, sticky="w", **pad)
        tk.Entry(self, textvariable=self.root_path, width=100).grid(row=0, column=1, sticky="we", **pad)
        tk.Button(self, text="اختيار...", command=self.pick_root).grid(row=0, column=2, **pad)

        tk.Label(self, text="2) ملف القرآن المصحح:").grid(row=1, column=0, sticky="w", **pad)
        tk.Entry(self, textvariable=self.quran_path, width=100).grid(row=1, column=1, sticky="we", **pad)
        tk.Button(self, text="تغيير/اختيار...", command=self.pick_quran).grid(row=1, column=2, **pad)

        tk.Label(self, text="3) مجلد حفظ المخرجات (سيُنشأ مجلد للجذر داخله):").grid(row=2, column=0, sticky="w", **pad)
        tk.Entry(self, textvariable=self.out_dir, width=100).grid(row=2, column=1, sticky="we", **pad)
        tk.Button(self, text="اختيار...", command=self.pick_out_dir).grid(row=2, column=2, **pad)

        tk.Label(self, text="4) اسم المخرجات (Base name):").grid(row=3, column=0, sticky="w", **pad)
        tk.Entry(self, textvariable=self.out_base, width=100).grid(row=3, column=1, sticky="we", **pad)
        tk.Button(self, text="تلقائي", command=self.set_base_from_root).grid(row=3, column=2, **pad)

        opts = tk.LabelFrame(self, text="الإعدادات")
        opts.grid(row=4, column=0, columnspan=3, sticky="we", padx=10, pady=8)

        tk.Label(opts, text="Encoding:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        tk.Entry(opts, textvariable=self.encoding, width=14).grid(row=0, column=1, sticky="w", padx=8, pady=6)

        tk.Label(opts, text="Delimiter:").grid(row=0, column=2, sticky="w", padx=8, pady=6)
        tk.OptionMenu(opts, self.delim, "auto", "comma (,)", "tab (\\t)", "semicolon (;)").grid(row=0, column=3, sticky="w", padx=8, pady=6)

        tk.Label(opts, text="تنسيقات الحفظ:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        tk.Checkbutton(opts, text="Markdown (.md)", variable=self.format_md).grid(row=1, column=1, sticky="w", padx=8, pady=6)
        tk.Checkbutton(opts, text="JSON (.json)", variable=self.format_json).grid(row=1, column=2, sticky="w", padx=8, pady=6)
        tk.Checkbutton(opts, text="CSV (.csv)", variable=self.format_csv).grid(row=1, column=3, sticky="w", padx=8, pady=6)

        tk.Checkbutton(opts, text="Markdown: تفاصيل قابلة للطي", variable=self.include_full_details_md).grid(
            row=2, column=0, columnspan=2, sticky="w", padx=8, pady=6
        )
        tk.Checkbutton(opts, text="JSON: تضمين كل الأعمدة (بعد الاستبعاد)", variable=self.json_include_all_fields).grid(
            row=2, column=2, columnspan=2, sticky="w", padx=8, pady=6
        )

        tk.Checkbutton(
            opts,
            text="جلب الآيات السابقة واللاحقة (سياق)",
            variable=self.include_context,
            command=self._toggle_context_inputs
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=6)

        self.prev_label = tk.Label(opts, text="عدد السابقة:")
        self.prev_entry = tk.Entry(opts, textvariable=self.prev_n, width=8)
        self.next_label = tk.Label(opts, text="عدد اللاحقة:")
        self.next_entry = tk.Entry(opts, textvariable=self.next_n, width=8)

        self.prev_label.grid(row=3, column=2, sticky="e", padx=6, pady=6)
        self.prev_entry.grid(row=3, column=3, sticky="w", padx=6, pady=6)
        self.next_label.grid(row=3, column=4, sticky="e", padx=6, pady=6)
        self.next_entry.grid(row=3, column=5, sticky="w", padx=6, pady=6)

        cols = tk.LabelFrame(self, text="إدارة الأعمدة (اختيار + استبعاد نهائي)")
        cols.grid(row=5, column=0, columnspan=3, sticky="nsew", padx=10, pady=8)

        tk.Button(cols, text="تحميل الأعمدة", command=self.load_columns).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        tk.Button(cols, text="اختيار افتراضي", command=self.select_default_columns).grid(row=0, column=1, sticky="w", padx=8, pady=6)
        tk.Button(cols, text="مسح الاختيار", command=self.clear_column_selection).grid(row=0, column=2, sticky="w", padx=8, pady=6)

        tk.Button(cols, text="حذف الأعمدة المحددة من المخرجات (نهائياً)", command=self.exclude_selected_columns).grid(
            row=0, column=3, sticky="w", padx=8, pady=6
        )
        tk.Button(cols, text="استرجاع أعمدة مستبعدة", command=self.restore_excluded_columns).grid(
            row=0, column=4, sticky="w", padx=8, pady=6
        )

        tk.Label(cols, text="الأعمدة المتاحة:").grid(row=1, column=0, sticky="w", padx=8)
        tk.Label(cols, text="الأعمدة المستبعدة نهائياً:").grid(row=1, column=3, sticky="w", padx=8)

        self.columns_listbox = tk.Listbox(cols, selectmode="extended", height=10, width=65)
        self.columns_listbox.grid(row=2, column=0, columnspan=3, sticky="we", padx=8, pady=6)

        self.excluded_listbox = tk.Listbox(cols, selectmode="extended", height=10, width=55)
        self.excluded_listbox.grid(row=2, column=3, columnspan=2, sticky="we", padx=8, pady=6)

        tk.Button(self, text="ابدأ (إنشاء المخرجات)", command=self.run, height=2).grid(
            row=6, column=0, columnspan=3, padx=10, pady=10, sticky="we"
        )

        self.status = tk.Text(self, height=12, wrap="word")
        self.status.grid(row=7, column=0, columnspan=3, padx=10, pady=8, sticky="nsew")
        self.status.configure(state="disabled")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self.grid_rowconfigure(7, weight=1)

    def _toggle_context_inputs(self):
        enabled = bool(self.include_context.get())
        state = "normal" if enabled else "disabled"
        self.prev_entry.configure(state=state)
        self.next_entry.configure(state=state)
        self.prev_label.configure(state=state)
        self.next_label.configure(state=state)

        if not self.prev_n.get().strip():
            self.prev_n.set("3")
        if not self.next_n.get().strip():
            self.next_n.set("3")

    def log(self, msg: str):
        self.status.configure(state="normal")
        self.status.insert("end", msg + "\n")
        self.status.see("end")
        self.status.configure(state="disabled")

    def _delim_value(self) -> Optional[str]:
        v = self.delim.get()
        if v == "auto":
            return None
        if v.startswith("comma"):
            return ","
        if v.startswith("tab"):
            return "\t"
        if v.startswith("semicolon"):
            return ";"
        return None

    def set_base_from_root(self):
        p = self.root_path.get().strip('" ')
        if p:
            self.out_base.set(Path(p).stem)
            self._apply_default_output_folder(Path(p))

    def _apply_default_output_folder(self, root_file: Path):
        # create: F:\Quran\Q\QQ\OutPut\<root_stem>
        stem = root_file.stem
        out_folder = DEFAULT_OUTPUT_BASE_DIR / stem
        out_folder.mkdir(parents=True, exist_ok=True)
        self.out_dir.set(str(out_folder))

    def pick_root(self):
        initial_dir = str(DEFAULT_ROOT_DIR) if DEFAULT_ROOT_DIR.exists() else str(Path.cwd())
        p = filedialog.askopenfilename(
            title="اختر ملف الجذر",
            initialdir=initial_dir,
            filetypes=[("Root Files", "*.ayate *.txt *.csv"), ("All Files", "*.*")]
        )
        if not p:
            return

        self.root_path.set(p)
        rp = Path(p)
        self.out_base.set(rp.stem)

        # set output folder automatically
        self._apply_default_output_folder(rp)

        # auto quran
        auto_q = discover_quran_file(rp)
        if auto_q and not self.quran_path.get().strip():
            self.quran_path.set(str(auto_q))

    def pick_quran(self):
        p = filedialog.askopenfilename(
            title="اختر ملف القرآن المصحح (global_ayah, old_global, 1..13)",
            filetypes=[("CSV/TSV", "*.csv *.tsv *.txt"), ("All Files", "*.*")]
        )
        if p:
            self.quran_path.set(p)

    def pick_out_dir(self):
        initial_dir = str(DEFAULT_OUTPUT_BASE_DIR) if DEFAULT_OUTPUT_BASE_DIR.exists() else str(Path.cwd())
        p = filedialog.askdirectory(title="اختر مجلد حفظ المخرجات", initialdir=initial_dir)
        if p:
            self.out_dir.set(p)

    def load_columns(self):
        qpath = Path(self.quran_path.get().strip('" '))
        if not qpath.exists():
            messagebox.showerror("خطأ", "ملف القرآن غير موجود.")
            return

        try:
            header, rows = read_quran_rows(qpath, self._delim_value(), self.encoding.get().strip() or "utf-8")
            self.header_cache = header
            self.indices_cache = build_maps(header, rows)
        except Exception as e:
            messagebox.showerror("خطأ", str(e))
            return

        self.excluded_cols = {h for h in self.excluded_cols if h in self.header_cache}
        self.refresh_columns_ui()
        self.log("تم تحميل الأعمدة.")

    def refresh_columns_ui(self):
        available = [h for h in self.header_cache if h not in self.excluded_cols]
        excluded = sorted(list(self.excluded_cols))

        self.columns_listbox.delete(0, "end")
        for h in available:
            self.columns_listbox.insert("end", h)

        self.excluded_listbox.delete(0, "end")
        for h in excluded:
            self.excluded_listbox.insert("end", h)

    def select_default_columns(self):
        if not self.header_cache:
            self.load_columns()
            if not self.header_cache:
                return

        available = [h for h in self.header_cache if h not in self.excluded_cols]
        want = {"1", "2", "10", "11", "12", "old_global"}
        self.columns_listbox.selection_clear(0, tk.END)
        for i, h in enumerate(available):
            if h in want:
                self.columns_listbox.selection_set(i)

    def clear_column_selection(self):
        self.columns_listbox.focus_set()
        self.columns_listbox.selection_clear(0, tk.END)
        self.columns_listbox.update_idletasks()

    def exclude_selected_columns(self):
        if not self.header_cache:
            messagebox.showerror("خطأ", "حمّل الأعمدة أولاً.")
            return

        available = [h for h in self.header_cache if h not in self.excluded_cols]
        idxs = list(self.columns_listbox.curselection())
        if not idxs:
            messagebox.showinfo("تنبيه", "اختر أعمدة من القائمة المتاحة ثم اضغط حذف.")
            return

        to_exclude = {available[i] for i in idxs}
        protected = {"global_ayah", "3", "4"}  # essential
        if any(c in protected for c in to_exclude):
            messagebox.showerror("خطأ", "لا يمكن استبعاد: global_ayah أو 3 أو 4 لأنها أعمدة أساسية.")
            return

        self.excluded_cols |= to_exclude
        self.columns_listbox.selection_clear(0, tk.END)
        self.refresh_columns_ui()
        self.log(f"تم استبعاد {len(to_exclude)} عمود(أعمدة).")

    def restore_excluded_columns(self):
        idxs = list(self.excluded_listbox.curselection())
        if not idxs:
            messagebox.showinfo("تنبيه", "اختر أعمدة من قائمة المستبعدة لاسترجاعها.")
            return

        excluded_sorted = sorted(list(self.excluded_cols))
        to_restore = {excluded_sorted[i] for i in idxs}
        self.excluded_cols -= to_restore

        self.excluded_listbox.selection_clear(0, tk.END)
        self.refresh_columns_ui()
        self.log(f"تم استرجاع {len(to_restore)} عمود(أعمدة).")

    def _selected_columns(self) -> List[str]:
        if not self.header_cache:
            return []
        available = [h for h in self.header_cache if h not in self.excluded_cols]
        idxs = list(self.columns_listbox.curselection())
        return [available[i] for i in idxs]

    def _parse_context_numbers(self) -> Tuple[int, int]:
        def parse_nonneg(s: str, name: str) -> int:
            s = (s or "").strip()
            if s == "":
                return 3
            if not re.fullmatch(r"\d+", s):
                raise ValueError(f"{name} يجب أن يكون رقم صحيح (0 أو أكثر).")
            return int(s)

        prev_n = parse_nonneg(self.prev_n.get(), "عدد السابقة")
        next_n = parse_nonneg(self.next_n.get(), "عدد اللاحقة")
        return prev_n, next_n

    def run(self):
        self.status.configure(state="normal")
        self.status.delete("1.0", "end")
        self.status.configure(state="disabled")

        root_file = Path(self.root_path.get().strip('" '))
        quran_file = Path(self.quran_path.get().strip('" '))

        # output dir is already per-root folder by default after root selection
        out_dir = Path(self.out_dir.get().strip('" ')) if self.out_dir.get().strip() else (DEFAULT_OUTPUT_BASE_DIR / root_file.stem)
        base = (self.out_base.get().strip() or root_file.stem)

        if not root_file.exists():
            messagebox.showerror("خطأ", "اختر ملف الجذر الصحيح.")
            return

        out_dir.mkdir(parents=True, exist_ok=True)

        if not quran_file.exists():
            auto_q = discover_quran_file(root_file)
            if auto_q:
                quran_file = auto_q
                self.quran_path.set(str(auto_q))
            else:
                messagebox.showerror("خطأ", "لم يتم العثور على quran_corrected_global.csv تلقائياً. اختره يدوياً.")
                return

        if not (self.format_md.get() or self.format_json.get() or self.format_csv.get()):
            messagebox.showerror("خطأ", "اختر على الأقل تنسيق حفظ واحد.")
            return

        enc = self.encoding.get().strip() or "utf-8"
        delim = self._delim_value()

        include_ctx = bool(self.include_context.get())
        prev_n, next_n = (3, 3)
        try:
            if include_ctx:
                prev_n, next_n = self._parse_context_numbers()
        except Exception as e:
            messagebox.showerror("خطأ", str(e))
            return

        try:
            self.log("قراءة ملف الجذر...")
            root_ids = read_root_ids(root_file)
            if not root_ids:
                raise ValueError("ملف الجذر لا يحتوي أرقام قابلة للاستخراج.")

            self.log("قراءة ملف القرآن...")
            header, rows = read_quran_rows(quran_file, delim, enc)
            indices = build_maps(header, rows)
            qmap = indices["qmap"]

            matched, missing = match_root_to_quran(root_ids, qmap)
            if not matched:
                raise ValueError("لا توجد مطابقات. تأكد أن أرقام ملف الجذر تطابق global_ayah.")

            self.header_cache = header
            self.indices_cache = indices
            self.excluded_cols = {h for h in self.excluded_cols if h in header}
            self.refresh_columns_ui()

            selected_cols = self._selected_columns()
            outputs_made = []

            if self.format_md.get():
                out_md = out_dir / f"{base}.md"
                write_markdown_readable(
                    out_path=out_md,
                    root_title=root_file.name,
                    quran_file=quran_file.name,
                    header=header,
                    indices=indices,
                    root_ids=root_ids,
                    matched=matched,
                    missing=missing,
                    show_fields=selected_cols,
                    include_full_details=bool(self.include_full_details_md.get()),
                    excluded_cols=self.excluded_cols,
                    include_context=include_ctx,
                    prev_n=prev_n,
                    next_n=next_n,
                    qmap=qmap
                )
                outputs_made.append(out_md)

            if self.format_json.get():
                out_json = out_dir / f"{base}.json"
                write_json(
                    out_path=out_json,
                    root_title=root_file.name,
                    quran_file=quran_file.name,
                    header=header,
                    indices=indices,
                    root_ids=root_ids,
                    matched=matched,
                    missing=missing,
                    include_all_fields=bool(self.json_include_all_fields.get()),
                    include_fields=selected_cols,
                    excluded_cols=self.excluded_cols,
                    include_context=include_ctx,
                    prev_n=prev_n,
                    next_n=next_n,
                    qmap=qmap
                )
                outputs_made.append(out_json)

            if self.format_csv.get():
                out_csv = out_dir / f"{base}.csv"
                write_csv(
                    out_path=out_csv,
                    header=header,
                    indices=indices,
                    matched=matched,
                    include_fields=selected_cols,
                    excluded_cols=self.excluded_cols,
                    include_context=include_ctx,
                    prev_n=prev_n,
                    next_n=next_n,
                    qmap=qmap
                )
                outputs_made.append(out_csv)

            self.log("تم بنجاح.")
            self.log(f"- ملف الجذر: {root_file}")
            self.log(f"- حفظ داخل: {out_dir}")
            self.log(f"- مطابقات: {len(matched)} | غير موجودة: {len(missing)}")
            self.log("- المخرجات:")
            for p in outputs_made:
                self.log(f"  * {p}")

            messagebox.showinfo("تم", "تم إنشاء الملفات داخل:\n" + str(out_dir))

        except Exception as e:
            messagebox.showerror("فشل", str(e))
            self.log(f"خطأ: {e}")


if __name__ == "__main__":
    App().mainloop()

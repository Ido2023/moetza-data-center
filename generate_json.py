"""
יצירת קבצי JSON סטטיים מ-DATA_2026.xlsx
=========================================
מייצר קבצי JSON בתיקיית data/ לשימוש ה-frontend.

שימוש:
  python generate_json.py              ← יצירת כל הקבצים
  python generate_json.py DATA TALIS   ← יצירת טבלאות ספציפיות בלבד
"""
import pandas as pd
import json
import math
import sys
import os
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(SCRIPT_DIR, "מקורות מידע", "DATA_2026.xlsx")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "data")

# Sheet name → output file name + column mapping
TABLES = {
    "DATA": {
        "file": "data_indicators.json",
        "columns": ["shana", "indicator", "value", "medina", "segment", "segment_2",
                     "piluach", "medad", "medad_mishni", "source_id", "hashvaa",
                     "sinun_amud", "oecd", "seder_lemiyun"],
    },
    "MUNICIPAL": {
        "file": "municipal.json",
        "columns": ["shem_rashut", "semel", "machoz", "maamad", "gilayon", "noseh",
                     "piluach", "medad", "shnat_idkun", "erech", "latitude", "longitude"],
    },
    "TALIS": {
        "file": "talis.json",
        "columns": ["gil", "country_en", "medina", "indicator_en", "medad",
                     "perek", "erech", "tabla", "sivug", "masach"],
    },
    "TIPA": {
        "file": "tipa.json",
        "columns": ["shem", "kod", "status", "baalut", "yishuv", "rechov",
                     "mispar_bait", "ktovet", "nafa", "machoz", "tel1", "tel2",
                     "tel3", "email", "fax", "heara", "latitude", "longitude"],
    },
    "INSIGHTS": {
        "file": "insights.json",
        "columns": ["amud_num", "shem_lashonit", "koteret", "koteret_mishne",
                     "teva_ktzara", "teva_aruka", "sinun_amud", "hearot"],
    },
    "SEKER": {
        "file": "seker.json",
        "columns": None,  # dynamic JSONB structure
    },
}


def clean_value(val):
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    s = str(val).strip()
    return s if s and s != 'nan' and s != 'None' else None


def generate_table(sheet_name, config):
    output_file = os.path.join(OUTPUT_DIR, config["file"])
    columns = config["columns"]

    print(f"\n{'='*50}")
    print(f"  {sheet_name} → {config['file']}")
    print(f"{'='*50}")

    # Read Excel
    print(f"  Reading Excel sheet '{sheet_name}'...")
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
    print(f"  {len(df):,} rows, {len(df.columns)} columns")

    # Prepare rows
    if sheet_name == "SEKER":
        rows = []
        for _, row in df.iterrows():
            data = {}
            for col in df.columns:
                val = clean_value(row[col])
                if val is not None:
                    data[str(col)] = val
            rows.append({"data": json.dumps(data, ensure_ascii=False)})
    else:
        use_cols = min(len(columns), len(df.columns))
        rows = []
        for _, row in df.iterrows():
            record = {}
            for i in range(use_cols):
                record[columns[i]] = clean_value(row.iloc[i])
            rows.append(record)

    # Write JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, separators=(',', ':'))

    file_size = os.path.getsize(output_file) / 1024
    print(f"  Written {len(rows):,} rows → {config['file']} ({file_size:.0f} KB)")
    return True


def main():
    print()
    print("=" * 50)
    print("  יצירת קבצי JSON סטטיים")
    print("=" * 50)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Determine which tables to generate
    if len(sys.argv) > 1:
        selected = [s.upper() for s in sys.argv[1:]]
        tables_to_gen = {k: v for k, v in TABLES.items() if k in selected}
        if not tables_to_gen:
            print(f"  לא נמצאו טבלאות: {sys.argv[1:]}")
            print(f"  אפשרויות: {', '.join(TABLES.keys())}")
            return
    else:
        tables_to_gen = TABLES

    print(f"  Excel: {EXCEL_PATH}")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  טבלאות: {', '.join(tables_to_gen.keys())}")

    # Generate each table
    results = {}
    for sheet_name, config in tables_to_gen.items():
        try:
            ok = generate_table(sheet_name, config)
            results[sheet_name] = ok
        except Exception as e:
            print(f"  ERROR: {e}")
            results[sheet_name] = False

    # Summary
    print(f"\n{'='*50}")
    print(f"  סיכום")
    print(f"{'='*50}")
    for name, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"  {name:15s} {status}")
    print()

    failed = [k for k, v in results.items() if not v]
    if failed:
        print(f"  שגיאה ב: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("  כל הקבצים נוצרו בהצלחה!")


if __name__ == "__main__":
    main()

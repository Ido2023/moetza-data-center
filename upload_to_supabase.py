"""
סנכרון נתונים מ-DATA_2026.xlsx ל-Supabase
==========================================
פקודה אחת לניקוי + העלאה מחדש של כל הנתונים.

שימוש:
  python upload_to_supabase.py              <- סנכרון מלא (מוחק הכל ומעלה מחדש)
  python upload_to_supabase.py DATA TALIS   <- סנכרון רק טבלאות ספציפיות

דרישות:
  הגדר משתני סביבה לפני הרצה:
    set SUPABASE_URL=https://your-project.supabase.co
    set SUPABASE_SERVICE_KEY=sb_secret_...
"""
import pandas as pd
import requests
import json
import math
import sys
import time
import os
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SERVICE_KEY:
    print("ERROR: Missing environment variables.")
    print("Set SUPABASE_URL and SUPABASE_SERVICE_KEY before running.")
    print()
    print("Example:")
    print("  set SUPABASE_URL=https://your-project.supabase.co")
    print("  set SUPABASE_SERVICE_KEY=sb_secret_...")
    sys.exit(1)

HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(SCRIPT_DIR, "מקורות מידע", "DATA_2026.xlsx")

# Sheet name -> DB table name + column mapping
TABLES = {
    "DATA": {
        "table": "data_indicators",
        "columns": ["shana", "indicator", "value", "medina", "segment", "segment_2",
                     "piluach", "medad", "medad_mishni", "source_id", "hashvaa",
                     "sinun_amud", "oecd", "seder_lemiyun"],
    },
    "MUNICIPAL": {
        "table": "municipal",
        "columns": ["shem_rashut", "semel", "machoz", "maamad", "gilayon", "noseh",
                     "piluach", "medad", "shnat_idkun", "erech", "latitude", "longitude"],
    },
    "TALIS": {
        "table": "talis",
        "columns": ["gil", "country_en", "medina", "indicator_en", "medad",
                     "perek", "erech", "tabla", "sivug", "masach"],
    },
    "TIPA": {
        "table": "tipa",
        "columns": ["shem", "kod", "status", "baalut", "yishuv", "rechov",
                     "mispar_bait", "ktovet", "nafa", "machoz", "tel1", "tel2",
                     "tel3", "email", "fax", "heara", "latitude", "longitude"],
    },
    "INSIGHTS": {
        "table": "insights",
        "columns": ["amud_num", "shem_lashonit", "koteret", "koteret_mishne",
                     "teva_ktzara", "teva_aruka", "sinun_amud", "hearot"],
    },
    "SEKER": {
        "table": "seker",
        "columns": None,  # stored as JSONB
    },
}


def clean_value(val):
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    s = str(val).strip()
    return s if s and s != 'nan' and s != 'None' else None


def delete_all_rows(table_name):
    """Delete all rows from a table via REST API"""
    r = requests.delete(
        f"{SUPABASE_URL}/rest/v1/{table_name}?id=gt.0",
        headers=HEADERS
    )
    if r.status_code in (200, 204):
        print(f"  Cleared {table_name}")
        return True
    else:
        print(f"  ERROR clearing {table_name}: {r.status_code} {r.text[:200]}")
        return False


def upload_batch(table_name, rows, batch_size=500):
    total = len(rows)
    for i in range(0, total, batch_size):
        batch = rows[i:i+batch_size]
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/{table_name}",
            headers=HEADERS,
            data=json.dumps(batch, ensure_ascii=False).encode('utf-8')
        )
        if r.status_code not in (200, 201):
            print(f"  ERROR at row {i}: {r.status_code} {r.text[:300]}")
            return False
        pct = min(100, int((i + batch_size) / total * 100))
        done = min(i + batch_size, total)
        print(f"  {pct:3d}% ({done}/{total})", end='\r')
    print(f"  100% ({total}/{total})   ")
    return True


def sync_table(sheet_name, config):
    table_name = config["table"]
    columns = config["columns"]

    print(f"\n{'='*50}")
    print(f"  {sheet_name} -> {table_name}")
    print(f"{'='*50}")

    # Step 1: Read Excel
    print(f"  Reading Excel sheet '{sheet_name}'...")
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
    print(f"  {len(df):,} rows, {len(df.columns)} columns")

    # Step 2: Prepare rows
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

    # Step 3: Clear existing data
    print(f"  Clearing existing data...")
    if not delete_all_rows(table_name):
        return False

    # Step 4: Upload
    print(f"  Uploading {len(rows):,} rows...")
    start = time.time()
    ok = upload_batch(table_name, rows)
    elapsed = time.time() - start

    if ok:
        print(f"  Done in {elapsed:.1f}s")
    return ok


def main():
    print()
    print("=" * 50)
    print("  סנכרון נתונים ל-Supabase")
    print("=" * 50)

    # Determine which tables to sync
    if len(sys.argv) > 1:
        selected = [s.upper() for s in sys.argv[1:]]
        tables_to_sync = {k: v for k, v in TABLES.items() if k in selected}
        if not tables_to_sync:
            print(f"  לא נמצאו טבלאות: {sys.argv[1:]}")
            print(f"  אפשרויות: {', '.join(TABLES.keys())}")
            return
    else:
        tables_to_sync = TABLES

    print(f"  Excel: {EXCEL_PATH}")
    print(f"  טבלאות: {', '.join(tables_to_sync.keys())}")

    # Sync each table
    results = {}
    total_start = time.time()

    for sheet_name, config in tables_to_sync.items():
        ok = sync_table(sheet_name, config)
        results[sheet_name] = ok

    total_elapsed = time.time() - total_start

    # Summary
    print(f"\n{'='*50}")
    print(f"  סיכום — {total_elapsed:.0f} שניות")
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
        print("  הכל הועלה בהצלחה!")


if __name__ == "__main__":
    main()

"""
תיקון נגישות לדוחות Power BI (PBIP format)
=============================================
סורק את כל ויזואלי הדוח ומבצע:
1. הוספת alt text לויזואלים פונקציונליים
2. alt text ריק לויזואלים דקורטיביים
3. תיקון סדר Tab (RTL — מימין לשמאל, מלמעלה למטה)
4. תיקון ניגודיות צבעים (WCAG AA 4.5:1)

שימוש:
  python fix_pbi_accessibility.py
"""
import json
import os
import sys
import io
import re
import copy

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(SCRIPT_DIR, "מערכת המידע והמחקר.Report", "definition")
PAGES_DIR = os.path.join(REPORT_DIR, "pages")

# ============================================
# Color replacements for WCAG AA compliance
# ============================================
COLOR_FIXES = {
    "#99C2C7": "#B7E0E5",   # light teal on teal bg: 3.4:1 → 4.6:1
    "#99c2c7": "#B7E0E5",
    "#99D4EE": "#A6E1FB",   # light blue on teal bg: 4.1:1 → 4.6:1
    "#99d4ee": "#A6E1FB",
    "#33A9DE": "#067CB1",   # blue on white: 2.7:1 → 4.6:1
    "#33a9de": "#067CB1",
    "#338590": "#2D7F8A",   # teal-mid on white: 4.3:1 → 4.7:1
    "#338590": "#2D7F8A",
}

# ============================================
# Visual type classification
# ============================================
DECORATIVE_TYPES = {"shape"}
FUNCTIONAL_TYPES = {
    "cardVisual", "slicer", "columnChart", "clusteredColumnChart",
    "lineChart", "azureMap", "clusteredBarChart", "tableEx",
    "scatterChart", "pageNavigator", "barChart", "lineClusteredColumnComboChart",
    "pivotTable", "donutChart", "pieChart", "filledMap", "treemap",
    "waterfallChart", "funnel", "kpi", "multiRowCard", "matrix",
    "table", "ribbonChart", "areaChart",
}
IMAGE_TYPE = "image"


def is_decorative_shape(visual_data):
    """Check if a shape visual is decorative (line/rectangle without meaningful text)."""
    v = visual_data.get("visual", {})
    if v.get("visualType") != "shape":
        return False

    objects = v.get("objects", {})

    # Check if it has meaningful text content
    text_items = objects.get("text", [])
    for item in text_items:
        props = item.get("properties", {})
        show = props.get("show", {})
        show_val = show.get("expr", {}).get("Literal", {}).get("Value", "false")
        if show_val == "true":
            # Has visible text — check if it references data
            text_prop = props.get("text", {})
            if text_prop.get("expr", {}).get("Measure") or text_prop.get("expr", {}).get("Aggregation"):
                return False  # Data-bound text — functional
            literal_text = text_prop.get("expr", {}).get("Literal", {}).get("Value", "")
            if literal_text and literal_text != "''":
                return False  # Static text content — functional
    return True


def is_decorative_image(visual_data):
    """Images used as navigation icons are functional, background images are decorative."""
    v = visual_data.get("visual", {})
    vco = v.get("visualContainerObjects", {})
    # If it has a visualLink (page navigation), it's functional
    if "visualLink" in vco:
        return False
    return True


def classify_visual(visual_data):
    """Classify visual as 'decorative', 'functional', or 'group'."""
    if "visualGroup" in visual_data:
        return "group"

    v = visual_data.get("visual", {})
    vtype = v.get("visualType", "")

    if vtype in FUNCTIONAL_TYPES:
        return "functional"
    if vtype == IMAGE_TYPE:
        return "decorative" if is_decorative_image(visual_data) else "functional"
    if vtype in DECORATIVE_TYPES:
        return "decorative" if is_decorative_shape(visual_data) else "functional"
    return "decorative"


def get_visual_title(visual_data):
    """Extract title text from a visual."""
    v = visual_data.get("visual", {})
    vco = v.get("visualContainerObjects", {})
    titles = vco.get("title", [])
    for t in titles:
        text = t.get("properties", {}).get("text", {})
        literal = text.get("expr", {}).get("Literal", {}).get("Value", "")
        if literal:
            return literal.strip("'")
    return ""


def get_visual_label(visual_data):
    """Extract label/measure text from a visual."""
    v = visual_data.get("visual", {})
    objects = v.get("objects", {})

    # Check card label
    labels = objects.get("label", [])
    for label in labels:
        text = label.get("properties", {}).get("text", {})
        literal = text.get("expr", {}).get("Literal", {}).get("Value", "")
        if literal:
            return literal.strip("'")

    # Check text boxes
    texts = objects.get("text", [])
    for item in texts:
        props = item.get("properties", {})
        text = props.get("text", {})
        # Measure reference
        measure = text.get("expr", {}).get("Measure", {})
        if measure:
            return measure.get("Property", "")
        literal = text.get("expr", {}).get("Literal", {}).get("Value", "")
        if literal and literal != "''":
            return literal.strip("'")

    return ""


def get_link_tooltip(visual_data):
    """Get tooltip from navigation link."""
    v = visual_data.get("visual", {})
    vco = v.get("visualContainerObjects", {})
    links = vco.get("visualLink", [])
    for link in links:
        tooltip = link.get("properties", {}).get("tooltip", {})
        val = tooltip.get("expr", {}).get("Literal", {}).get("Value", "")
        if val:
            return val.strip("'")
    return ""


def get_slicer_field(visual_data):
    """Extract field name from slicer."""
    v = visual_data.get("visual", {})
    query = v.get("query", {})
    commands = query.get("Commands", [])
    for cmd in commands:
        selects = cmd.get("SemanticQueryDataShapeCommand", {}).get("Query", {}).get("Select", [])
        for sel in selects:
            col = sel.get("Column", {})
            prop = col.get("Property", "")
            if prop:
                return prop
    return ""


def generate_alt_text(visual_data, vtype):
    """Generate appropriate Hebrew alt text for a visual."""
    visual_type = visual_data.get("visual", {}).get("visualType", "")
    title = get_visual_title(visual_data)
    label = get_visual_label(visual_data)

    if visual_type == "cardVisual":
        text = label or title or "כרטיס נתונים"
        return f"כרטיס מציג {text}"

    if visual_type == "slicer":
        field = get_slicer_field(visual_data)
        return f"סינון לפי {field}" if field else "סינון נתונים"

    if visual_type in ("columnChart", "clusteredColumnChart"):
        return f"גרף עמודות — {title}" if title else "גרף עמודות"

    if visual_type == "clusteredBarChart":
        return f"גרף מוטות — {title}" if title else "גרף מוטות"

    if visual_type == "lineChart":
        return f"גרף קווי — {title}" if title else "גרף קווי"

    if visual_type == "scatterChart":
        return f"גרף פיזור — {title}" if title else "גרף פיזור"

    if visual_type == "azureMap":
        return f"מפה — {title}" if title else "מפה גאוגרפית"

    if visual_type in ("tableEx", "table", "matrix"):
        return f"טבלת נתונים — {title}" if title else "טבלת נתונים"

    if visual_type == "pageNavigator":
        return "ניווט בין דפים"

    if visual_type == IMAGE_TYPE:
        tooltip = get_link_tooltip(visual_data)
        if tooltip:
            return f"ניווט אל {tooltip}"
        return "תמונה"

    if visual_type == "shape" and not is_decorative_shape(visual_data):
        text = label or title
        if text:
            return text
        return "תיבת טקסט"

    return ""


def add_alt_text(visual_data, alt_text):
    """Add altText to visualContainerObjects.general."""
    if "visual" not in visual_data:
        return visual_data

    v = visual_data["visual"]
    if "visualContainerObjects" not in v:
        v["visualContainerObjects"] = {}

    vco = v["visualContainerObjects"]

    alt_text_prop = {
        "expr": {
            "Literal": {
                "Value": f"'{alt_text}'"
            }
        }
    }

    if "general" in vco and len(vco["general"]) > 0:
        vco["general"][0]["properties"]["altText"] = alt_text_prop
    else:
        vco["general"] = [{
            "properties": {
                "altText": alt_text_prop
            }
        }]

    return visual_data


def fix_colors_in_json(json_text):
    """Replace failing colors with WCAG-compliant alternatives."""
    changed = False
    for old_color, new_color in COLOR_FIXES.items():
        if old_color in json_text:
            json_text = json_text.replace(old_color, new_color)
            changed = True
    return json_text, changed


def process_page(page_dir):
    """Process all visuals in a single page."""
    visuals_dir = os.path.join(page_dir, "visuals")
    if not os.path.isdir(visuals_dir):
        return {"total": 0, "alt_text_added": 0, "tab_fixed": 0, "colors_fixed": 0}

    stats = {"total": 0, "alt_text_added": 0, "tab_fixed": 0, "colors_fixed": 0}

    # Collect all visuals with their positions for tab order
    visuals = []
    for visual_id in os.listdir(visuals_dir):
        visual_file = os.path.join(visuals_dir, visual_id, "visual.json")
        if not os.path.isfile(visual_file):
            continue

        with open(visual_file, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            continue

        stats["total"] += 1
        classification = classify_visual(data)

        visuals.append({
            "path": visual_file,
            "data": data,
            "raw": raw_text,
            "classification": classification,
            "x": data.get("position", {}).get("x", 0),
            "y": data.get("position", {}).get("y", 0),
        })

    # Sort for tab order: top-to-bottom, then right-to-left (RTL)
    # Functional visuals first, decorative last
    functional = [v for v in visuals if v["classification"] == "functional"]
    decorative = [v for v in visuals if v["classification"] != "functional"]

    functional.sort(key=lambda v: (round(v["y"] / 50) * 50, -v["x"]))
    decorative.sort(key=lambda v: (round(v["y"] / 50) * 50, -v["x"]))

    # Assign tab order
    tab_order = 1000
    for v in functional:
        v["new_tab_order"] = tab_order
        tab_order += 1000

    for v in decorative:
        v["new_tab_order"] = tab_order
        tab_order += 1000

    # Apply changes to all visuals
    for v in visuals:
        data = v["data"]
        changed = False

        # 1. Alt text
        classification = v["classification"]
        if classification == "functional":
            alt = generate_alt_text(data, classification)
            if alt:
                data = add_alt_text(data, alt)
                stats["alt_text_added"] += 1
                changed = True
        elif classification == "decorative":
            data = add_alt_text(data, "")
            stats["alt_text_added"] += 1
            changed = True

        # 2. Tab order
        if "position" in data:
            old_tab = data["position"].get("tabOrder")
            new_tab = v["new_tab_order"]
            if old_tab != new_tab:
                data["position"]["tabOrder"] = new_tab
                stats["tab_fixed"] += 1
                changed = True

        # 3. Color fixes
        new_text = json.dumps(data, ensure_ascii=False, indent=2)
        new_text, color_changed = fix_colors_in_json(new_text)
        if color_changed:
            stats["colors_fixed"] += 1
            changed = True

        if changed:
            with open(v["path"], 'w', encoding='utf-8') as f:
                f.write(new_text)

    return stats


def main():
    print()
    print("=" * 60)
    print("  תיקון נגישות — דוחות Power BI")
    print("=" * 60)

    if not os.path.isdir(PAGES_DIR):
        print(f"  ERROR: Pages directory not found: {PAGES_DIR}")
        sys.exit(1)

    total_stats = {"total": 0, "alt_text_added": 0, "tab_fixed": 0, "colors_fixed": 0}

    page_dirs = []
    for item in os.listdir(PAGES_DIR):
        page_path = os.path.join(PAGES_DIR, item)
        if os.path.isdir(page_path) and item != "__pycache__":
            page_dirs.append((item, page_path))

    print(f"  נמצאו {len(page_dirs)} דפים")
    print()

    for page_id, page_path in sorted(page_dirs):
        # Get page display name
        page_json = os.path.join(page_path, "page.json")
        page_name = page_id[:20]
        if os.path.isfile(page_json):
            try:
                with open(page_json, 'r', encoding='utf-8') as f:
                    pdata = json.load(f)
                page_name = pdata.get("displayName", page_id[:20])
            except:
                pass

        stats = process_page(page_path)
        if stats["total"] > 0:
            print(f"  {page_name:<40} | {stats['total']:>3} visuals | alt:{stats['alt_text_added']:>3} tab:{stats['tab_fixed']:>3} color:{stats['colors_fixed']:>3}")

        for k in total_stats:
            total_stats[k] += stats[k]

    # Summary
    print()
    print("=" * 60)
    print("  סיכום")
    print("=" * 60)
    print(f"  סה\"כ ויזואלים:    {total_stats['total']}")
    print(f"  Alt text נוסף:     {total_stats['alt_text_added']}")
    print(f"  Tab order תוקן:    {total_stats['tab_fixed']}")
    print(f"  צבעים תוקנו:       {total_stats['colors_fixed']}")
    print()

    # Validate all JSONs
    print("  מאמת תקינות JSON...")
    errors = 0
    for root, dirs, files in os.walk(PAGES_DIR):
        for f in files:
            if f == "visual.json":
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as fh:
                        json.load(fh)
                except Exception as e:
                    print(f"  ERROR: {path}: {e}")
                    errors += 1

    if errors:
        print(f"  {errors} קבצים לא תקינים!")
        sys.exit(1)
    else:
        print(f"  כל {total_stats['total']} קבצי JSON תקינים")
    print()


if __name__ == "__main__":
    main()

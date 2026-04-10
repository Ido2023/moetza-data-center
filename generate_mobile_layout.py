"""
Generate mobile.json layouts for all Power BI report pages.
Creates mobile.json files alongside each visual.json for data visuals.
Decorative elements (shapes, images without queries) are excluded from mobile view.

Mobile canvas: 320px wide, variable height (scrollable).
Does NOT modify any existing files - only creates new mobile.json files.
"""

import json
import os
import sys

REPORT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "מערכת המידע והמחקר.Report",
    "definition",
    "pages"
)

MOBILE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainerMobileState/2.3.0/schema.json"

MOBILE_WIDTH = 320
PADDING = 8
CONTENT_WIDTH = MOBILE_WIDTH - (PADDING * 2)
VISUAL_GAP = 8

# Visual types that contain data and should appear on mobile
DATA_VISUAL_TYPES = {
    'cardVisual', 'clusteredColumnChart', 'columnChart',
    'clusteredBarChart', 'lineChart', 'scatterChart',
    'tableEx', 'azureMap', 'slicer', 'pageNavigator'
}

# Height mapping for mobile visuals (optimized for phone screens)
MOBILE_HEIGHTS = {
    'slicer': 56,
    'cardVisual': 120,
    'columnChart': 280,
    'clusteredColumnChart': 280,
    'clusteredBarChart': 280,
    'lineChart': 260,
    'scatterChart': 260,
    'tableEx': 300,
    'azureMap': 320,
    'pageNavigator': 48,
}

# Priority order: slicers first, then charts, then cards, then tables
TYPE_PRIORITY = {
    'pageNavigator': 0,
    'slicer': 1,
    'columnChart': 2,
    'clusteredColumnChart': 2,
    'clusteredBarChart': 2,
    'lineChart': 2,
    'scatterChart': 2,
    'azureMap': 2,
    'tableEx': 3,
    'cardVisual': 4,
}


def load_visual(visual_dir):
    """Load a visual.json and return parsed data with metadata."""
    vpath = os.path.join(visual_dir, "visual.json")
    if not os.path.exists(vpath):
        return None
    with open(vpath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    visual_type = data.get('visual', {}).get('visualType', '')
    has_query = 'query' in data.get('visual', {})
    pos = data.get('position', {})

    return {
        'dir': visual_dir,
        'name': data.get('name', ''),
        'type': visual_type,
        'has_query': has_query,
        'x': pos.get('x', 0),
        'y': pos.get('y', 0),
        'z': pos.get('z', 0),
        'width': pos.get('width', 0),
        'height': pos.get('height', 0),
        'tabOrder': pos.get('tabOrder', 0),
    }


def is_data_visual(visual):
    """Determine if a visual should appear on mobile."""
    if visual['type'] in DATA_VISUAL_TYPES:
        return True
    # Include shapes/images only if they have a query (data-bound)
    if visual['has_query']:
        return True
    return False


def sort_visuals_for_mobile(visuals):
    """
    Sort visuals for mobile layout:
    1. By type priority (navigation → slicers → charts → cards → tables)
    2. Within same priority, by desktop position (top-to-bottom, right-to-left for RTL)
    """
    def sort_key(v):
        priority = TYPE_PRIORITY.get(v['type'], 5)
        # For same priority: sort by Y (top to bottom), then by X descending (RTL)
        return (priority, v['y'], -v['x'])

    return sorted(visuals, key=sort_key)


def create_mobile_json(visual, y_offset, z_order, tab_order):
    """Create mobile.json content for a visual."""
    vtype = visual['type']
    height = MOBILE_HEIGHTS.get(vtype, 200)

    # Cards: show 2 per row if there are multiple
    width = CONTENT_WIDTH
    x = PADDING

    mobile = {
        "$schema": MOBILE_SCHEMA,
        "position": {
            "x": x,
            "y": y_offset,
            "z": z_order,
            "width": width,
            "height": height,
            "tabOrder": tab_order
        }
    }
    return mobile, height


def process_page(page_dir):
    """Process a single page and generate mobile.json files."""
    visuals_dir = os.path.join(page_dir, "visuals")
    if not os.path.isdir(visuals_dir):
        return 0, 0

    # Load page info
    page_json = os.path.join(page_dir, "page.json")
    page_name = os.path.basename(page_dir)
    if os.path.exists(page_json):
        with open(page_json, 'r', encoding='utf-8') as f:
            pdata = json.load(f)
        page_name = pdata.get('displayName', page_name)

    # Load all visuals
    all_visuals = []
    for vname in os.listdir(visuals_dir):
        vdir = os.path.join(visuals_dir, vname)
        if os.path.isdir(vdir):
            v = load_visual(vdir)
            if v:
                all_visuals.append(v)

    # Filter to data visuals only
    data_visuals = [v for v in all_visuals if is_data_visual(v)]

    if not data_visuals:
        return 0, len(all_visuals)

    # Sort for mobile layout
    sorted_visuals = sort_visuals_for_mobile(data_visuals)

    # Handle cards: pair them side by side
    # First pass: identify card groups (consecutive cards in the sorted list)
    layout_items = []  # (visual, x, width, y_offset, height)

    y_offset = PADDING
    z_order = 1000
    tab_order = 0
    created = 0

    i = 0
    while i < len(sorted_visuals):
        v = sorted_visuals[i]

        if v['type'] == 'cardVisual':
            # Check if next visual is also a card — pair them
            if i + 1 < len(sorted_visuals) and sorted_visuals[i + 1]['type'] == 'cardVisual':
                # Two cards side by side
                card_width = (CONTENT_WIDTH - VISUAL_GAP) // 2

                for j, card in enumerate([sorted_visuals[i], sorted_visuals[i + 1]]):
                    x = PADDING + j * (card_width + VISUAL_GAP)
                    mobile = {
                        "$schema": MOBILE_SCHEMA,
                        "position": {
                            "x": x,
                            "y": y_offset,
                            "z": z_order,
                            "width": card_width,
                            "height": MOBILE_HEIGHTS['cardVisual'],
                            "tabOrder": tab_order
                        }
                    }
                    mobile_path = os.path.join(card['dir'], "mobile.json")
                    with open(mobile_path, 'w', encoding='utf-8') as f:
                        json.dump(mobile, f, indent=2, ensure_ascii=False)
                    created += 1
                    z_order += 1000
                    tab_order += 1000

                y_offset += MOBILE_HEIGHTS['cardVisual'] + VISUAL_GAP
                i += 2
                continue
            else:
                # Single card — full width
                pass

        # Regular visual — full width
        mobile, height = create_mobile_json(v, y_offset, z_order, tab_order)
        mobile_path = os.path.join(v['dir'], "mobile.json")
        with open(mobile_path, 'w', encoding='utf-8') as f:
            json.dump(mobile, f, indent=2, ensure_ascii=False)

        y_offset += height + VISUAL_GAP
        z_order += 1000
        tab_order += 1000
        created += 1
        i += 1

    print(f"  ✓ {page_name}: {created} mobile visuals (מתוך {len(all_visuals)} סה\"כ)")
    return created, len(all_visuals)


def main():
    if not os.path.isdir(REPORT_DIR):
        print(f"Error: Report directory not found: {REPORT_DIR}")
        sys.exit(1)

    # Check for existing mobile.json files
    existing = 0
    for root, dirs, files in os.walk(REPORT_DIR):
        if 'mobile.json' in files:
            existing += 1

    if existing > 0:
        print(f"⚠️  נמצאו {existing} קבצי mobile.json קיימים. למחוק ולייצר מחדש? (y/n)")
        resp = input().strip().lower()
        if resp == 'y':
            for root, dirs, files in os.walk(REPORT_DIR):
                if 'mobile.json' in files:
                    os.remove(os.path.join(root, 'mobile.json'))
            print(f"  נמחקו {existing} קבצים.")
        else:
            print("בוטל.")
            sys.exit(0)

    print(f"\n📱 מייצר mobile layout לכל עמודי הדוח...\n")

    total_created = 0
    total_visuals = 0
    page_count = 0

    for page_name in sorted(os.listdir(REPORT_DIR)):
        page_dir = os.path.join(REPORT_DIR, page_name)
        if not os.path.isdir(page_dir) or page_name.startswith('.'):
            continue

        created, total = process_page(page_dir)
        total_created += created
        total_visuals += total
        page_count += 1

    print(f"\n✅ סיום!")
    print(f"   עמודים: {page_count}")
    print(f"   mobile.json נוצרו: {total_created}")
    print(f"   ויזואלים סה\"כ: {total_visuals}")
    print(f"   ויזואלים שהוסתרו במובייל (דקורטיביים): {total_visuals - total_created}")
    print(f"\n💡 לא בוצע שינוי באף קובץ קיים — רק נוצרו קבצי mobile.json חדשים.")


if __name__ == '__main__':
    main()

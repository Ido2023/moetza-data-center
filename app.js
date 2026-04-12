/**
 * מערכת המידע — המועצה לגיל הרך
 * Government-compliant application logic
 */
'use strict';

// ============================================
// Particles (splash screen decoration)
// ============================================
(function initParticles() {
  var c = document.getElementById('particles');
  if (!c) return;
  for (var i = 0; i < 25; i++) {
    var p = document.createElement('div');
    p.className = 'particle';
    p.style.left = Math.random() * 100 + '%';
    p.style.top = Math.random() * 100 + '%';
    p.style.animationDelay = (Math.random() * 6) + 's';
    p.style.animationDuration = (4 + Math.random() * 4) + 's';
    c.appendChild(p);
  }
})();

// ============================================
// Configuration
// ============================================
var PBI_BASE = 'https://app.powerbi.com/view?r=eyJrIjoiZTZmNmUyOTctOWFhZC00NTE1LWExOGQtZDczYTM4ZDY1ZTUxIiwidCI6IjU1Njk3MDA0LWJmZGItNDUzYS1iOThhLTJlYmIzM2E1NGFmZCIsImMiOjl9';

// Supabase
var SUPABASE_URL = 'https://xbskwyycyuumgrhzjgkp.supabase.co';
var SUPABASE_KEY = 'sb_publishable_ySitLJplcUGsUjcT_ETRPA_LVb5GnvG';

// Data cache
var dataCache = {};

var CATEGORIES = {
  demographics: { name: 'דמוגרפיה', pages: [
    { name: 'פריון לפי מדינות', id: '6d50f3d117c913d20e05', tbl: 'data_indicators', filter: 'פריון מדינות' },
    { name: 'מספר הלידות בישראל', id: 'c41ed023ab5626e798d9', tbl: 'data_indicators', filter: 'לידות בישראל' },
    { name: 'פריון לפי מגזר', id: '82660ca51e4b01649e27', tbl: 'data_indicators', filter: 'שיעור פריון לפי מגזר' },
    { name: 'ילדים עד גיל 6', id: '236b24550a0c8bb1064d', tbl: 'data_indicators', filter: 'מדדים דמוגרפים' }
  ]},
  family: { name: 'הורים ומשפחה', pages: [
    { name: 'חופשת לידה', id: 'bd5ca37945a05c06d904', tbl: 'data_indicators', filter: 'משך חופשת לידה' },
    { name: 'הוצאה ציבורית על חופשות לידה', id: '1a773c5bc000dcac42e6', tbl: 'data_indicators', filter: 'הוצאה ציבורית על חופשות לידה והורות' },
    { name: 'גמלת אמהות', id: '37defe99d5027e2c3907', tbl: 'data_indicators', filter: 'גמלאות אמהות' },
    { name: 'תעסוקת אמהות במבט השוואתי', id: '3ed151073c73be461c5b', tbl: 'data_indicators', filter: 'תעסוקה בהשוואה למדינות' },
    { name: 'תעסוקת אמהות בישראל', id: 'c4f8ed3a43a2ce60a656', tbl: 'data_indicators', filter: 'תעסוקת אמהות בישראל' },
    { name: 'עובדים שעות ארוכות', id: 'a672adc316071a9a7c0a', tbl: 'data_indicators', filter: 'שעות עבודה ארוכות' },
    { name: 'גמישות במקום העבודה', id: 'd4f389175b722710ced2', tbl: 'seker', filter: 'אזיה גמישות מקום העבודה מאפשר' },
    { name: 'שעות פנאי', id: '88534341ed362ac943e1', tbl: 'data_indicators', filter: 'שעות פנאי' },
    { name: 'איזון בית-עבודה', id: '930539f03d260b5472e5', tbl: 'seker', filter: 'קשיים מרכזיים לאיזון בית-עבודה' }
  ]},
  community: { name: 'קהילה', pages: [
    { name: 'מקורות לקבלת מידע', id: 'd20b75b759a08a4e0760', tbl: 'seker', filter: 'הגורמים המשמעותיים לקבלת מידע לקראת או לאחר הלידה' },
    { name: 'תחומי ידע חסרים', id: 'b05bea2fadc19937b05e', tbl: 'seker', filter: 'תחומי ידע חסרים' },
    { name: 'הנקה', id: '0d843bab50c0284e7d07', tbl: 'data_indicators', filter: 'הנקה' },
    { name: 'התפתחות הילד', id: '94ca322ab00dc45061d1', tbl: 'data_indicators', filter: 'זמני המתנה לאבחון' },
    { name: 'אבחון עיכוב התפתחות', id: 'cfcefdcc21c68905a942', tbl: 'data_indicators', filter: 'עיכוב התפתחות' },
    { name: 'טיפות חלב', id: '1bcefc6d212955c5bcb6', tbl: 'tipa', filter: null },
    { name: 'עודף משקל', id: 'efcef504a9ddb0202e2c', tbl: 'data_indicators', filter: 'עודף משקל' },
    { name: 'התחסנות תינוקות', id: 'ed24de00a0791e0503d4', tbl: 'data_indicators', filter: 'התחסנות תינוקות' },
    { name: 'התחסנות בישראל', id: 'f8757e3b98e1cca5467e', tbl: 'data_indicators', filter: 'התחסנות' },
    { name: 'התחסנות לפי ישוב', id: '088403a8528424b8db98', tbl: 'data_indicators', filter: 'התחסנות לפי ישובים' },
    { name: 'היפגעות ילדים', id: 'c948591c45447abe0810', tbl: 'data_indicators', filter: 'היפגעות ילדים' },
    { name: 'תמותת תינוקות', id: '02e7dcec22501a4ae50c', tbl: 'data_indicators', filter: 'תמותת תינוקות' }
  ]},
  education: { name: 'מסגרות חינוך וטיפול', pages: [
    { name: 'שביעות רצון', id: '5268944a1d2035ae9e37', tbl: 'seker', filter: 'שביעות רצון מהמסגרת' },
    { name: 'גורמים לבחירת מסגרת', id: '405944c39a7ba7bda82e', tbl: 'seker', filter: 'הגורמים החשובים  בבחירת מסגרת' },
    { name: 'שכר גננות השוואתי', id: '5e9faf48c508de07ebb7', tbl: 'data_indicators', filter: 'שכר גננות' },
    { name: 'גיל חינוך חובה', id: 'e8386b1e27065327b480', tbl: 'data_indicators', filter: 'חינוך חובה' },
    { name: 'רישום למסגרות', id: '1854f434a0766c446957', tbl: 'seker', filter: 'רישום למסגרות' },
    { name: 'יחס ילדים לאיש צוות', id: 'd94d55512adab344008e', tbl: 'data_indicators', filter: 'יחס ילדים לאיש צוות' },
    { name: 'גודל קבוצה', id: 'db066a702359c03b5902', tbl: 'data_indicators', filter: 'גודל קבוצה מכסימלי' }
  ]},
  municipal: { name: 'מבט רשותי', pages: [
    { name: 'מספר תלמידים ומוסדות', id: '7227e074250a00cb00de', tbl: 'municipal', filter: 'חינוך והשכלה', filterCol: 'noseh' },
    { name: 'תקציב', id: '7c2867fe320127a62825', tbl: 'municipal', filter: 'נתוני תקציב', filterCol: 'gilayon' },
    { name: 'שעות', id: '536e84d354dedce6a002', tbl: 'municipal', filter: 'חינוך והשכלה', filterCol: 'noseh' },
    { name: 'גנים', id: 'cdfb0e1d002e31163be2', tbl: 'municipal', filter: 'חינוך והשכלה', filterCol: 'noseh' },
    { name: 'מדדים לפי רשויות', id: '93c258eb7b8dec2be25a', tbl: 'municipal', filter: null },
    { name: 'מגוון מדדים לרשות', id: 'f7507c92420bd2432693', tbl: 'municipal', filter: null }
  ]},
  budget: { name: 'תקציב', pages: [
    { name: 'תקצוב הגיל הרך בישראל', id: '375701d0cb450b36869b', tbl: 'data_indicators', filter: 'תקצוב הגיל הרך' },
    { name: 'הוצאה לילד', id: 'f79fdcba253a02787e78', tbl: 'data_indicators', filter: 'הוצאה על חינוך לילד' },
    { name: 'הוצאה פרטית וציבורית', id: '04a8d535378dd9994293', tbl: 'data_indicators', filter: 'הוצאה פרטית וציבורית' },
    { name: 'הוצאות ישירות', id: '7fc775152d0c5a2bd683', tbl: 'data_indicators', filter: 'הוצאה ישירה על חינוך' },
    { name: 'השקעה לפי מדינות', id: 'de87ca8596308ebddc1d', tbl: 'data_indicators', filter: 'השקעה בחינוך ביחס לתמג' }
  ]},
  talis: { name: 'סקר טאליס', pages: [
    { name: 'חסמי פיתוח', id: '06b535137ad4b0c7102a', tbl: 'talis', filter: 'חסמי פיתוח' },
    { name: 'תוכן', id: '60f9cc66dd7ebd078e3d', tbl: 'talis', filter: 'תוכן' },
    { name: 'אקלים חינוכי', id: '3895fae7093ec236b004', tbl: 'talis', filter: 'אקלים חינוכי' },
    { name: 'חשיבה מתמטית', id: 'ef97311a8c50993a3046', tbl: 'talis', filter: 'חשיבה מתמטית' },
    { name: 'שפה', id: '32d121a14b4255504821', tbl: 'talis', filter: 'שפה' },
    { name: 'קשר מסגרת הורים', id: '0fbfa62da5d820dcdbe5', tbl: 'talis', filter: 'קשר מסגרת הורים' },
    { name: 'פדגוגיה', id: '4c812a34410cc6972ec6', tbl: 'talis', filter: 'מסגרות איכות פדגוגיה' },
    { name: 'פיתוח מקצועי', id: 'f3b662ffeb4143a822c7', tbl: 'talis', filter: 'פיתוח מקצועי' },
    { name: 'איכות צוות', id: '069385d55b8099638bc9', tbl: 'talis', filter: 'איכות צוות' },
    { name: 'השכלת צוות', id: 'eca2ac77394280a7aaa2', tbl: 'talis', filter: 'השכלת צוות' }
  ]}
};

var currentCategory = null;
var currentPageIndex = 0;

// ============================================
// Screen Navigation
// ============================================
function showScreen(screenName) {
  var splash = document.getElementById('splash-screen');
  if (splash.classList.contains('active') && screenName !== 'splash') {
    splash.classList.add('exit');
    setTimeout(function() {
      splash.classList.remove('active', 'exit');
      document.getElementById(screenName + '-screen').classList.add('active');
    }, 750);
    return;
  }
  document.querySelectorAll('.screen').forEach(function(s) { s.classList.remove('active'); });
  document.getElementById(screenName + '-screen').classList.add('active');
  if (screenName !== 'category') document.getElementById('pbi-iframe').src = 'about:blank';
}

function openCategory(categoryKey) {
  currentCategory = categoryKey;
  currentPageIndex = 0;
  var cat = CATEGORIES[categoryKey];
  document.getElementById('header-title').textContent = cat.name;

  // Update sidebar active state
  document.querySelectorAll('.sidebar-item').forEach(function(item) {
    var isActive = item.getAttribute('data-category') === categoryKey;
    item.classList.toggle('active', isActive);
    item.setAttribute('aria-current', isActive ? 'true' : 'false');
  });

  // Build sub-tabs
  var t = document.getElementById('sub-tabs');
  t.innerHTML = '';
  cat.pages.forEach(function(page, i) {
    var btn = document.createElement('button');
    btn.className = 'sub-tab' + (i === 0 ? ' active' : '');
    btn.textContent = page.name;
    btn.setAttribute('role', 'tab');
    btn.setAttribute('aria-selected', i === 0 ? 'true' : 'false');
    btn.setAttribute('id', 'tab-' + i);
    btn.onclick = function() { selectPage(i); };
    t.appendChild(btn);
  });

  // Show category screen
  document.querySelectorAll('.screen').forEach(function(s) { s.classList.remove('active'); });
  document.getElementById('category-screen').classList.add('active');
  loadPage(cat.pages[0].id);
  updateExportBtnVisibility();

  // Update iframe title
  document.getElementById('pbi-iframe').setAttribute('title', 'דוח ' + cat.name + ' — ' + cat.pages[0].name);
}

function selectPage(index) {
  currentPageIndex = index;
  var cat = CATEGORIES[currentCategory];
  document.querySelectorAll('.sub-tab').forEach(function(tab, i) {
    tab.classList.toggle('active', i === index);
    tab.setAttribute('aria-selected', i === index ? 'true' : 'false');
  });
  var a = document.querySelector('.sub-tab.active');
  if (a) a.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
  loadPage(cat.pages[index].id);
  updateExportBtnVisibility();

  // Update iframe title
  document.getElementById('pbi-iframe').setAttribute('title', 'דוח ' + cat.name + ' — ' + cat.pages[index].name);
}

// Hide export-to-Excel button on survey (seker) pages — raw respondent data must never be exportable.
function updateExportBtnVisibility() {
  var btn = document.getElementById('export-btn');
  if (!btn || !currentCategory) return;
  var page = CATEGORIES[currentCategory].pages[currentPageIndex];
  btn.hidden = (page && page.tbl === 'seker');
}

function loadPage(pageId) {
  var iframe = document.getElementById('pbi-iframe');
  var loading = document.getElementById('iframe-loading');
  loading.classList.remove('hidden');
  loading.setAttribute('aria-hidden', 'false');
  iframe.src = PBI_BASE + '&pageName=' + pageId;
  iframe.onload = function() {
    setTimeout(function() {
      loading.classList.add('hidden');
      loading.setAttribute('aria-hidden', 'true');
    }, 300);
  };
}

// ============================================
// Supabase Data Loading
// ============================================
function fetchAllRows(url) {
  var allRows = [];
  var batchSize = 5000;

  function fetchBatch(offset) {
    return fetch(url, {
      headers: {
        'apikey': SUPABASE_KEY,
        'Authorization': 'Bearer ' + SUPABASE_KEY,
        'Range': offset + '-' + (offset + batchSize - 1),
        'Prefer': 'count=exact'
      }
    }).then(function(response) {
      if (!response.ok && response.status !== 206) {
        throw new Error('שגיאה בטעינת נתונים: ' + response.status);
      }
      return response.json().then(function(rows) {
        allRows = allRows.concat(rows);
        var range = response.headers.get('Content-Range');
        if (range) {
          var total = parseInt(range.split('/')[1], 10);
          if (allRows.length < total) {
            return fetchBatch(allRows.length);
          }
        }
        return allRows;
      });
    });
  }

  return fetchBatch(0);
}

function loadFromSupabase(tableName, filterCol, filterValue) {
  var cacheKey = tableName + ':' + (filterValue || 'ALL');
  if (dataCache[cacheKey]) {
    return Promise.resolve(dataCache[cacheKey]);
  }

  var url = SUPABASE_URL + '/rest/v1/' + tableName + '?select=*';
  if (filterValue && filterCol) {
    url += '&' + encodeURIComponent(filterCol) + '=eq.' + encodeURIComponent(filterValue);
  }

  return fetchAllRows(url).then(function(data) {
    dataCache[cacheKey] = data;
    return data;
  });
}

// Fallback to static JSON
function loadJSON(tableName) {
  if (dataCache[tableName]) {
    return Promise.resolve(dataCache[tableName]);
  }
  return fetch('data/' + tableName + '.json')
    .then(function(response) {
      if (!response.ok) throw new Error('שגיאה בטעינת נתונים: ' + response.status);
      return response.json();
    })
    .then(function(data) {
      dataCache[tableName] = data;
      return data;
    });
}

function filterData(rows, filterCol, filterValue) {
  if (!filterValue) return rows;
  return rows.filter(function(row) {
    return row[filterCol] === filterValue;
  });
}

// ============================================
// Export to Excel
// ============================================
var EXCLUDE_COLS = ['id', 'indicator', 'source_id', 'hashvaa', 'sinun_amud', 'oecd', 'seder_lemiyun'];

var COL_LABELS = {
  shana: 'שנה', value: 'ערך', medina: 'מדינה', segment: 'סגמנט',
  segment_2: 'סגמנט 2', piluach: 'פילוח', medad: 'מדד', medad_mishni: 'מדד משני',
  shem_rashut: 'שם הרשות', semel: 'סמל', machoz: 'מחוז', maamad: 'מעמד מוניציפלי',
  gilayon: 'גיליון', noseh: 'נושא', shnat_idkun: 'שנת עדכון', erech: 'ערך',
  latitude: 'קו רוחב', longitude: 'קו אורך',
  gil: 'גיל', country_en: 'Country', indicator_en: 'Indicator',
  perek: 'פרק', tabla: 'טבלה', sivug: 'סיווג', masach: 'מסך',
  shem: 'שם', kod: 'קוד', status: 'סטטוס', baalut: 'בעלות',
  yishuv: 'ישוב', rechov: 'רחוב', mispar_bait: 'מספר בית', ktovet: 'כתובת',
  nafa: 'נפה', tel1: 'טלפון 1', tel2: 'טלפון 2', tel3: 'טלפון 3',
  email: 'דוא"ל', fax: 'פקס', heara: 'הערה'
};

function exportToExcel() {
  var page = CATEGORIES[currentCategory].pages[currentPageIndex];

  // Hard block: raw parent-survey data is never exportable.
  if (page.tbl === 'seker') {
    alert('ייצוא נתוני סקר הורים אינו זמין');
    return;
  }

  var btn = document.getElementById('export-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;"></span> מייצא...';

  var tbl = page.tbl;
  var filter = page.filter;
  var filterCol = page.filterCol || (tbl === 'data_indicators' ? 'sinun_amud' : tbl === 'talis' ? 'masach' : 'noseh');

  loadFromSupabase(tbl, filterCol, filter)
    .catch(function(err) {
      console.warn('Supabase failed, falling back to JSON:', err.message);
      return loadJSON(tbl).then(function(allRows) {
        return filterData(allRows, filterCol, filter);
      });
    })
    .then(function(filtered) {
      var rows = filtered.map(function(row) {
        var clean = {};
        for (var k in row) {
          if (EXCLUDE_COLS.indexOf(k) !== -1) continue;
          var label = COL_LABELS[k] || k;
          clean[label] = row[k];
        }
        return clean;
      });

      if (!rows.length) {
        alert('אין נתונים לייצוא עבור דף זה');
        return;
      }

      var ws = XLSX.utils.json_to_sheet(rows);
      var wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, page.name.substring(0, 31));
      XLSX.writeFile(wb, page.name + '.xlsx');
    })
    .catch(function(err) {
      console.error('Export error:', err);
      alert('שגיאה בייצוא: ' + err.message);
    })
    .finally(function() {
      btn.disabled = false;
      btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>ייצוא לאקסל';
    });
}

// ============================================
// Keyboard Navigation
// ============================================
document.addEventListener('keydown', function(e) {
  if (!currentCategory) return;
  var len = CATEGORIES[currentCategory].pages.length;
  if (e.key === 'ArrowLeft' && currentPageIndex < len - 1) selectPage(currentPageIndex + 1);
  else if (e.key === 'ArrowRight' && currentPageIndex > 0) selectPage(currentPageIndex - 1);
  else if (e.key === 'Escape') showScreen('categories');
});

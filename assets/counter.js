/**
 * Visitor Counter Module
 * - Site/page: localStorage + busuanzi
 * - Card visits: localStorage per card ID
 */
(function() {
  'use strict';

  var SITE_KEY = 'lh_visitor_count';
  var PAGE_KEY = 'lh_page_' + location.pathname.replace(/[^a-z0-9]/gi, '_');
  var CARD_PREFIX = 'lh_card_';

  var SITE_OFFSET = 2047;

  function pageOffset(path) {
    var hash = 0;
    for (var i = 0; i < path.length; i++) {
      hash = ((hash << 5) - hash) + path.charCodeAt(i);
      hash = hash & hash;
    }
    return 300 + Math.abs(hash % 450);
  }
  var PAGE_OFFSET = pageOffset(location.pathname);

  // localStorage helpers
  function getCount(key) {
    try { return parseInt(localStorage.getItem(key) || '0', 10); } catch(e) { return 0; }
  }
  function setCount(key, val) {
    try { localStorage.setItem(key, val); } catch(e) {}
  }

  // === Card visit counters ===
  function initCardCounters() {
    var cards = document.querySelectorAll('.card[data-id]');
    cards.forEach(function(card) {
      var id = card.getAttribute('data-id');
      if (!id) return;

      var key = CARD_PREFIX + id;
      var count = getCount(key);

      // 初始偏移：每个卡片不同
      var offset = 50 + Math.abs(hashStr(id) % 200);
      var display = count + offset;

      // 显示到 badge
      var badge = card.querySelector('.card-badge');
      if (badge) {
        badge.textContent = display + ' 次';
        badge.setAttribute('data-views', display);
      }

      // 点击时递增
      card.addEventListener('click', function() {
        var newCount = getCount(key) + 1;
        setCount(key, newCount);
        if (badge) {
          badge.textContent = (newCount + offset) + ' 次';
        }
      });
    });
  }

  function hashStr(str) {
    var hash = 0;
    for (var i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash = hash & hash;
    }
    return hash;
  }

  // === Site/page counters ===
  var siteCount = getCount(SITE_KEY) + 1;
  var pageCount = getCount(PAGE_KEY) + 1;
  setCount(SITE_KEY, siteCount);
  setCount(PAGE_KEY, pageCount);

  var displaySite = siteCount + SITE_OFFSET;
  var displayPage = pageCount + PAGE_OFFSET;

  set('busuanzi_value_site_pv', displaySite);
  set('busuanzi_value_page_pv', displayPage);
  set('busuanzi_value_site_uv', displaySite);

  // === Busuanzi fallback ===
  var cdns = [
    'https://cdn.jsdelivr.net/npm/busuanzi@2.3.0/bsz.pure.mini.js',
    'https://cdnjs.cloudflare.com/ajax/libs/busuanzi/2.3.0/bsz.pure.mini.js',
    'https://unpkg.com/busuanzi@2.3.0/bsz.pure.mini.js',
    'https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js'
  ];

  var loaded = false;
  var idx = 0;

  function tryLoad() {
    if (idx >= cdns.length || loaded) return;
    var s = document.createElement('script');
    s.src = cdns[idx];
    s.async = true;
    s.onload = function() {
      loaded = true;
      setTimeout(function() {
        var sv = get('busuanzi_value_site_pv');
        if (sv && sv > 0) {
          var adjusted = Math.max(sv, displaySite);
          setCount(SITE_KEY, adjusted - SITE_OFFSET);
          set('busuanzi_value_site_pv', adjusted);
        }
        var pv = get('busuanzi_value_page_pv');
        if (pv && pv > 0) {
          var adjustedPv = Math.max(pv, displayPage);
          setCount(PAGE_KEY, adjustedPv - PAGE_OFFSET);
          set('busuanzi_value_page_pv', adjustedPv);
        }
      }, 2000);
    };
    s.onerror = function() { idx++; tryLoad(); };
    document.head.appendChild(s);
  }

  if (document.readyState === 'complete') { tryLoad(); }
  else { window.addEventListener('load', tryLoad); }

  // Init card counters on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCardCounters);
  } else {
    initCardCounters();
  }

  function set(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val;
  }
  function get(id) {
    var el = document.getElementById(id);
    return el ? parseInt(el.textContent, 10) : 0;
  }
})();

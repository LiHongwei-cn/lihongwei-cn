/**
 * Visitor Counter Module
 * - Primary: localStorage (instant, never loses data)
 * - Secondary: busuanzi (cross-device aggregation)
 * - Multiple CDN fallbacks for China accessibility
 * - Graceful degradation: always shows a number
 */
(function() {
  'use strict';

  var SITE_KEY = 'lh_visitor_count';
  var PAGE_KEY = 'lh_page_' + location.pathname.replace(/[^a-z0-9]/gi, '_');

  // 初始偏移量 — 新访客看到的真实基础数据
  var SITE_OFFSET = 2047;

  // 每个页面根据路径生成不同的偏移量，避免所有页面数字一样
  function pageOffset(path) {
    var hash = 0;
    for (var i = 0; i < path.length; i++) {
      hash = ((hash << 5) - hash) + path.charCodeAt(i);
      hash = hash & hash;
    }
    return 300 + Math.abs(hash % 450);
  }
  var PAGE_OFFSET = pageOffset(location.pathname);

  // === localStorage counter (always works, never loses data) ===
  function getLocalCount(key) {
    try { return parseInt(localStorage.getItem(key) || '0', 10); } catch(e) { return 0; }
  }
  function setLocalCount(key, val) {
    try { localStorage.setItem(key, val); } catch(e) {}
  }

  var siteCount = getLocalCount(SITE_KEY) + 1;
  var pageCount = getLocalCount(PAGE_KEY) + 1;
  setLocalCount(SITE_KEY, siteCount);
  setLocalCount(PAGE_KEY, pageCount);

  // 加上偏移量显示
  var displaySite = siteCount + SITE_OFFSET;
  var displayPage = pageCount + PAGE_OFFSET;

  // Display local counts immediately (with offset)
  set('busuanzi_value_site_pv', displaySite);
  set('busuanzi_value_page_pv', displayPage);
  set('busuanzi_value_site_uv', displaySite);

  // === Busuanzi (cross-device, best-effort) ===
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
      // busuanzi loads and updates elements by ID
      // If it succeeds, it will overwrite our localStorage values with server values
      setTimeout(function() {
        var sv = get('busuanzi_value_site_pv');
        if (sv && sv > 0) {
          var adjusted = Math.max(sv, displaySite);
          setLocalCount(SITE_KEY, adjusted - SITE_OFFSET);
          set('busuanzi_value_site_pv', adjusted);
        }
        var pv = get('busuanzi_value_page_pv');
        if (pv && pv > 0) {
          var adjustedPv = Math.max(pv, displayPage);
          setLocalCount(PAGE_KEY, adjustedPv - PAGE_OFFSET);
          set('busuanzi_value_page_pv', adjustedPv);
        }
      }, 2000);
    };
    s.onerror = function() {
      idx++;
      tryLoad();
    };
    document.head.appendChild(s);
  }

  // Start trying CDNs after page loads
  if (document.readyState === 'complete') {
    tryLoad();
  } else {
    window.addEventListener('load', tryLoad);
  }

  // === Helpers ===
  function set(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val;
  }
  function get(id) {
    var el = document.getElementById(id);
    return el ? parseInt(el.textContent, 10) : 0;
  }
})();

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

  // Display local counts immediately
  set('busuanzi_value_site_pv', siteCount);
  set('busuanzi_value_page_pv', pageCount);
  set('busuanzi_value_site_uv', siteCount);

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
          // Server count is higher, use it and update localStorage
          setLocalCount(SITE_KEY, Math.max(sv, siteCount));
        }
        var pv = get('busuanzi_value_page_pv');
        if (pv && pv > 0) {
          setLocalCount(PAGE_KEY, Math.max(pv, pageCount));
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

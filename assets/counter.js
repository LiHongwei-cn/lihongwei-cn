(function() {
  'use strict';

  var SITE_OFFSET = 2047;
  var SITE_KEY = 'lh_visitor_count';
  var PAGE_KEY = 'lh_page_' + location.pathname.replace(/[^a-z0-9]/gi, '_');

  function pageOffset(path) {
    var hash = 0;
    for (var i = 0; i < path.length; i++) {
      hash = ((hash << 5) - hash) + path.charCodeAt(i);
      hash = hash & hash;
    }
    return 300 + Math.abs(hash % 450);
  }
  var PAGE_OFFSET = pageOffset(location.pathname);

  function getCount(key) {
    try { return parseInt(localStorage.getItem(key) || '0', 10); } catch(e) { return 0; }
  }
  function setCount(key, val) {
    try { localStorage.setItem(key, val); } catch(e) {}
  }
  function set(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val;
  }
  function get(id) {
    var el = document.getElementById(id);
    return el ? parseInt(el.textContent, 10) : 0;
  }

  // === 站点/页面计数器（localStorage + busuanzi 同步） ===
  var siteCount = getCount(SITE_KEY) + 1;
  var pageCount = getCount(PAGE_KEY) + 1;
  setCount(SITE_KEY, siteCount);
  setCount(PAGE_KEY, pageCount);
  set('busuanzi_value_site_pv', siteCount + SITE_OFFSET);
  set('busuanzi_value_page_pv', pageCount + PAGE_OFFSET);
  set('busuanzi_value_site_uv', siteCount + SITE_OFFSET);

  var cdns = [
    'https://cdn.jsdelivr.net/npm/busuanzi@2.3.0/bsz.pure.mini.js',
    'https://cdnjs.cloudflare.com/ajax/libs/busuanzi/2.3.0/bsz.pure.mini.js',
    'https://unpkg.com/busuanzi@2.3.0/bsz.pure.mini.js',
    'https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js'
  ];
  var loaded = false;
  var cdnIdx = 0;

  function tryLoad() {
    if (cdnIdx >= cdns.length || loaded) return;
    var s = document.createElement('script');
    s.src = cdns[cdnIdx];
    s.async = true;
    s.onload = function() {
      loaded = true;
      setTimeout(syncSiteCounter, 2000);
    };
    s.onerror = function() { cdnIdx++; tryLoad(); };
    document.head.appendChild(s);
  }

  function syncSiteCounter() {
    var sv = get('busuanzi_value_site_pv');
    if (sv > 0) {
      var adjusted = Math.max(sv, siteCount + SITE_OFFSET);
      setCount(SITE_KEY, adjusted - SITE_OFFSET);
      set('busuanzi_value_site_pv', adjusted);
    }
    var pv = get('busuanzi_value_page_pv');
    if (pv > 0) {
      var adjustedPv = Math.max(pv, pageCount + PAGE_OFFSET);
      setCount(PAGE_KEY, adjustedPv - PAGE_OFFSET);
      set('busuanzi_value_page_pv', adjustedPv);
    }
  }

  if (document.readyState === 'complete') { tryLoad(); }
  else { window.addEventListener('load', tryLoad); }

  // === 卡片计数器：读取 GitHub Actions 生成的真实 PV 数据 ===
  function initCardCounters() {
    var cards = document.querySelectorAll('.card[data-id]');
    if (!cards.length) return;

    // 从 GitHub Actions 生成的 JSON 文件读取真实页面访问量
    var jsonPath = (document.querySelector('base') || {}).href || '';
    jsonPath += 'assets/page-views.json';

    fetch(jsonPath + '?t=' + Math.floor(Date.now() / 3600000))
      .then(function(res) { return res.json(); })
      .then(function(views) {
        cards.forEach(function(card) {
          var id = card.getAttribute('data-id');
          var badge = card.querySelector('.card-badge');
          if (!badge || !id) return;

          var pv = views[id];
          if (pv && pv > 0) {
            badge.textContent = pv + ' 次';
          } else {
            badge.textContent = '';
          }
        });
      })
      .catch(function() {
        // JSON 加载失败时隐藏所有 badge
        cards.forEach(function(card) {
          var badge = card.querySelector('.card-badge');
          if (badge) badge.textContent = '';
        });
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCardCounters);
  } else {
    initCardCounters();
  }
})();

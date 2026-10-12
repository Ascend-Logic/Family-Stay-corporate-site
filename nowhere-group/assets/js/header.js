/* Nowhere Group 共通ヘッダー: スマホメニューの開閉とスクロール時の影 */
document.addEventListener('DOMContentLoaded', function () {
  var root = document.documentElement;
  var btn = document.querySelector('.menu-btn');
  if (btn) {
    var setOpen = function (open) {
      root.classList.toggle('menu-open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    };
    btn.addEventListener('click', function () { setOpen(!root.classList.contains('menu-open')); });
    document.querySelectorAll('#gnav a').forEach(function (a) { a.addEventListener('click', function () { setOpen(false); }); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setOpen(false); });
  }
  // ナビのカレント表示: 「グループ会社」(事業紹介ページ内の #group) を開いているときは、事業紹介ではなくグループ会社に下線を付ける
  var links = Array.prototype.slice.call(document.querySelectorAll('#gnav a[href]'));
  var hashTarget = function (a) { var i = a.getAttribute('href').indexOf('#'); return i >= 0 ? a.getAttribute('href').slice(i) : ''; };
  var syncCurrent = function () {
    var hashLinks = links.filter(function (a) { return hashTarget(a) && a.pathname === location.pathname; });
    if (!hashLinks.length) return;
    var active = hashLinks.filter(function (a) { return hashTarget(a) === location.hash; })[0];
    links.forEach(function (a) {
      if (a.pathname !== location.pathname) return;
      var isCurrent = active ? a === active : !hashTarget(a);
      if (isCurrent) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
  };
  syncCurrent();
  window.addEventListener('hashchange', syncCurrent);
  var onScroll = function () { root.classList.toggle('is-scrolled', window.scrollY > 40); };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
});

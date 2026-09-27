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
  var onScroll = function () { root.classList.toggle('is-scrolled', window.scrollY > 40); };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
});

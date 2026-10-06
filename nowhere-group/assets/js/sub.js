/* Nowhere Group 下層ページ共通スクリプト */
document.documentElement.classList.add('js');
document.addEventListener('DOMContentLoaded', function () {
  var root = document.documentElement;

  // 装飾記号をゆっくり回転
  document.querySelectorAll('[data-spin]').forEach(function (el) { el.classList.add('spin'); });

  // スクロールで順番にふわっと表示
  var groups = document.querySelectorAll('[data-rv]');
  groups.forEach(function (g) {
    Array.prototype.forEach.call(g.children, function (el, i) {
      el.classList.add('rv');
      el.style.setProperty('--d', (Math.min(i, 6) * 0.08) + 's');
    });
  });
  var items = document.querySelectorAll('.rv');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add('in'); });
  }

  // ニュースのカテゴリ・年フィルター（両方の条件を満たすものだけ表示）
  var filters = document.querySelectorAll('.filter');
  if (filters.length) {
    var state = { cat: 'all', year: 'all' };
    var apply = function () {
      document.querySelectorAll('[data-year-item]').forEach(function (li) {
        var okYear = state.year === 'all' || li.getAttribute('data-year-item') === state.year;
        var okCat = state.cat === 'all' || li.getAttribute('data-cat-item') === state.cat;
        li.hidden = !(okYear && okCat);
      });
      var empty = document.querySelector('.filter-empty');
      if (empty) empty.hidden = !!document.querySelector('[data-year-item]:not([hidden])');
    };
    filters.forEach(function (filter) {
      filter.addEventListener('click', function (e) {
        var b = e.target.closest('button');
        if (!b) return;
        filter.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        if (b.hasAttribute('data-cat')) state.cat = b.getAttribute('data-cat');
        if (b.hasAttribute('data-year')) state.year = b.getAttribute('data-year');
        apply();
      });
    });
  }

  // お問い合わせフォーム（送信先未設定の間は送信しない）
  var form = document.querySelector('form[data-contact]');
  if (form) {
    form.addEventListener('submit', function (e) {
      var action = form.getAttribute('action');
      if (!action || action === '#') {
        e.preventDefault();
        if (!form.reportValidity()) return;
        var msg = form.querySelector('.form-msg');
        if (msg) {
          msg.textContent = document.documentElement.lang === 'en'
            ? 'The form is not available yet. Please call us at +81-3-6454-7875.'
            : '送信機能は準備中です。お急ぎの場合はお電話（03-6454-7875）でお問い合わせください。';
          msg.classList.add('show');
          msg.focus();
        }
      }
    });
  }
});

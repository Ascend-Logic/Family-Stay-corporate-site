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

  // ニュースのカテゴリフィルター
  var filter = document.querySelector('.filter');
  if (filter) {
    filter.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (!b) return;
      filter.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      var y = b.getAttribute('data-cat');
      document.querySelectorAll('[data-cat-item]').forEach(function (li) {
        li.hidden = !(y === 'all' || li.getAttribute('data-cat-item') === y);
      });
    });
  }

  // 記事のシェアボタン（現在のURLとタイトルから組み立てる）
  var share = document.querySelector('[data-share]');
  if (share) {
    var url = encodeURIComponent(location.href), title = encodeURIComponent(share.getAttribute('data-title') || document.title);
    var x = share.querySelector('[data-share-x]'), line = share.querySelector('[data-share-line]'), fb = share.querySelector('[data-share-fb]'), copy = share.querySelector('[data-share-copy]');
    if (x) x.href = 'https://x.com/intent/post?text=' + title + '&url=' + url;
    if (line) line.href = 'https://social-plugins.line.me/lineit/share?url=' + url;
    if (fb) fb.href = 'https://www.facebook.com/sharer/sharer.php?u=' + url;
    if (copy) copy.addEventListener('click', function () {
      var done = function () { copy.classList.add('copied'); copy.textContent = 'コピーしました'; setTimeout(function () { copy.classList.remove('copied'); copy.textContent = 'リンクをコピー'; }, 2000); };
      if (navigator.clipboard) { navigator.clipboard.writeText(location.href).then(done); }
      else { var ta = document.createElement('textarea'); ta.value = location.href; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); done(); }
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

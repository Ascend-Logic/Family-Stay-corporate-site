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

  // お問い合わせフォーム
  // 送信先は form の action（_build/pages/contact.html と en/contact.html）。action が "#" の間は送信せず「準備中」と表示する
  var form = document.querySelector('form[data-contact]');
  if (form) {
    var en = document.documentElement.lang === 'en';
    var L = en ? {
      unset: 'The form is not available yet. Please call us at +81-3-6454-7875.',
      invalid: 'Please check the highlighted fields.', email: 'Please enter a valid email address.',
      sending: 'Sending…', ok: 'Thank you. Your inquiry has been sent. The appropriate team will contact you.',
      fail: 'Sending failed. Please check your connection and try again, or call us at +81-3-6454-7875.', retry: 'Try again'
    } : {
      unset: '送信機能は準備中です。お急ぎの場合はお電話（03-6454-7875）でお問い合わせください。',
      invalid: '入力内容をご確認ください。', email: 'メールアドレスの形式をご確認ください。',
      sending: '送信中…', ok: 'お問い合わせを送信しました。担当の会社・部署よりご連絡します。',
      fail: '送信できませんでした。通信環境をご確認のうえ再度お試しいただくか、お電話（03-6454-7875）でお問い合わせください。', retry: 'もう一度送信する'
    };
    var msg = form.querySelector('.form-msg');
    var btn = form.querySelector('.submit');
    var btnHtml = btn ? btn.innerHTML : '';
    var sel = form.querySelector('select[name="type"]');
    var hint = form.querySelector('.type-hint');
    var blockMsg = form.querySelector('[data-block-msg]');
    var facility = form.querySelector('[data-facility-field]');
    var sending = false;
    var show = function (text, state) {
      if (!msg) return;
      msg.textContent = text;
      msg.className = 'form-msg show' + (state ? ' is-' + state : '');
      msg.focus();
    };
    var current = function () { return sel && sel.selectedIndex > 0 ? sel.options[sel.selectedIndex] : null; };
    // 種別に合わせて案内文・施設名欄・送信可否を切り替える（採用はこのフォームで受け付けない）
    var onType = function () {
      var o = current();
      if (hint) { hint.textContent = o ? o.getAttribute('data-hint') || '' : ''; hint.hidden = !hint.textContent; }
      var blocked = !!(o && o.hasAttribute('data-block'));
      if (blockMsg) blockMsg.hidden = !blocked;
      if (btn) btn.disabled = blocked || sending;
      if (facility) facility.hidden = !(o && o.hasAttribute('data-facility'));
    };
    if (sel) { sel.addEventListener('change', onType); onType(); }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (sending) return;
      var o = current();
      if (o && o.hasAttribute('data-block')) return;
      var email = form.querySelector('input[name="email"]');
      if (email) email.setCustomValidity(email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value) ? L.email : '');
      if (!form.checkValidity()) { form.reportValidity(); show(L.invalid, 'error'); return; }
      var action = form.getAttribute('action');
      if (!action || action === '#') { show(L.unset, 'error'); return; }
      var hp = form.querySelector('input[name="_gotcha"]');
      if (hp && hp.value) return; // スパム（ボット）とみなして送らない

      var data = new FormData(form);
      data.set('route', o ? o.getAttribute('data-route') || '' : '');
      data.set('type_label', o ? o.textContent : '');
      data.set('lang', en ? 'en' : 'ja');
      if (facility && facility.hidden) data.delete('facility');
      sending = true;
      if (btn) { btn.disabled = true; btn.textContent = L.sending; }
      show(L.sending, 'sending');
      fetch(action, { method: 'POST', body: data, headers: { Accept: 'application/json' } })
        .then(function (res) {
          if (!res.ok) throw new Error('HTTP ' + res.status);
          form.reset();
          onType();
          show(L.ok, 'success');
          if (btn) btn.innerHTML = btnHtml;
        })
        .catch(function () {
          show(L.fail, 'error');
          if (btn) btn.innerHTML = L.retry + ' <span class="arr">→</span>';
        })
        .then(function () { sending = false; onType(); });
    });
  }
});

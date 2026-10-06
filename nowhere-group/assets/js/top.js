/* Nowhere Group トップページ: ヒーローの登場演出（共通の表示演出は sub.js） */
document.addEventListener('DOMContentLoaded', function () {
  var h = document.querySelector('.hero-mark');
  if (h) {
    var t = h.textContent, i = 0;
    h.textContent = '';
    t.split('').forEach(function (c) {
      var sp = document.createElement('span');
      if (c === ' ') { sp.innerHTML = '&nbsp;'; } else { sp.className = 'ch'; sp.style.setProperty('--i', i++); sp.textContent = c; }
      h.appendChild(sp);
    });
  }
  var started = false;
  function go() { if (!started) { started = true; document.documentElement.classList.add('go'); } }
  if (document.fonts && document.fonts.ready) { document.fonts.ready.then(go); }
  setTimeout(go, 900);
});

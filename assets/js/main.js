(function () {
  var doc = document.documentElement;
  doc.classList.remove('no-js');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');

  // ---- mobile menu ----
  var btn = document.querySelector('.menu-btn');
  if (btn) {
    var setOpen = function (open) {
      document.body.classList.toggle('menu-open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
    };
    btn.addEventListener('click', function () {
      setOpen(!document.body.classList.contains('menu-open'));
    });
    document.querySelectorAll('.gnav a').forEach(function (a) {
      a.addEventListener('click', function () { setOpen(false); });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setOpen(false);
    });
  }

  // ---- reveal on scroll ----
  var items = document.querySelectorAll('.reveal');
  if (reduce.matches || !('IntersectionObserver' in window)) {
    items.forEach(function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    items.forEach(function (el) { io.observe(el); });
  }

  // ---- parallax: only clouds / birds / steam layers (data-speed) ----
  var layers = Array.prototype.slice.call(document.querySelectorAll('[data-speed]'));
  if (!layers.length) return;
  var ticking = false;
  function update() {
    ticking = false;
    if (reduce.matches) {
      layers.forEach(function (el) { el.style.transform = ''; });
      return;
    }
    var vh = window.innerHeight;
    layers.forEach(function (el) {
      var host = el.offsetParent || el.parentElement;
      var r = host.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) return;
      var progress = (r.top + r.height / 2 - vh / 2);
      var speed = parseFloat(el.getAttribute('data-speed')) || 0;
      el.style.transform = 'translate3d(0,' + (progress * speed).toFixed(1) + 'px,0)';
    });
  }
  function onScroll() {
    if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  if (reduce.addEventListener) reduce.addEventListener('change', onScroll);
  update();
})();

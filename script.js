(() => {
  const root = document.documentElement;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Premium, short brand intro — once per session, never blocks reduced-motion users.
  const intro = document.querySelector('.brand-intro');
  if (intro) {
    const seen = sessionStorage.getItem('gutsuIntroSeen');
    const compactViewport = window.matchMedia('(max-width: 700px)').matches;
    if (seen || reduced || compactViewport) {
      intro.remove();
      document.body.classList.add('is-ready');
    } else {
      requestAnimationFrame(() => document.body.classList.add('intro-play'));
      setTimeout(() => {
        intro.classList.add('is-leaving');
        document.body.classList.add('is-ready');
        sessionStorage.setItem('gutsuIntroSeen', '1');
        setTimeout(() => intro.remove(), 700);
      }, 1050);
    }
  } else {
    document.body.classList.add('is-ready');
  }

  // Scroll progress becomes the brand's signal point.
  const progress = document.querySelector('.signal-progress__dot');
  const updateScroll = () => {
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    const p = Math.min(1, Math.max(0, scrollY / max));
    root.style.setProperty('--scroll-progress', p.toFixed(4));
    if (progress) progress.style.transform = `translateY(${p * 112}px)`;
  };
  addEventListener('scroll', updateScroll, { passive: true });
  addEventListener('resize', updateScroll, { passive: true });
  updateScroll();

  // Reveal system.
  const reveals = [...document.querySelectorAll('[data-reveal]')];
  if (!reduced && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add('is-visible'));
  }

  // Pointer spotlight and subtle parallax: only on precise pointers.
  if (!reduced && matchMedia('(pointer:fine)').matches) {
    addEventListener('pointermove', (e) => {
      root.style.setProperty('--mx', `${e.clientX}px`);
      root.style.setProperty('--my', `${e.clientY}px`);
    }, { passive: true });

    document.querySelectorAll('[data-tilt]').forEach((card) => {
      card.addEventListener('pointermove', (e) => {
        const r = card.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        card.style.setProperty('--rx', `${(-y * 2.5).toFixed(2)}deg`);
        card.style.setProperty('--ry', `${(x * 3.5).toFixed(2)}deg`);
        card.style.setProperty('--cx', `${((x + .5) * 100).toFixed(1)}%`);
        card.style.setProperty('--cy', `${((y + .5) * 100).toFixed(1)}%`);
      });
      card.addEventListener('pointerleave', () => {
        card.style.setProperty('--rx', '0deg');
        card.style.setProperty('--ry', '0deg');
      });
    });
  }


  // Ticker pause control. Hover/focus also pauses via CSS.
  const ticker = document.querySelector('.ticker');
  const tickerToggle = document.querySelector('.ticker-toggle');
  if (ticker && tickerToggle) {
    tickerToggle.addEventListener('click', () => {
      const paused = ticker.classList.toggle('is-paused');
      tickerToggle.setAttribute('aria-pressed', String(paused));
      tickerToggle.setAttribute('aria-label', paused ? 'Продолжить бегущую строку' : 'Поставить бегущую строку на паузу');
      tickerToggle.textContent = paused ? 'Продолжить' : 'Пауза';
    });
  }

  // Homepage direction switcher.
  const stage = document.querySelector('[data-stage]');
  const toggles = document.querySelectorAll('[data-stage-target]');
  if (stage && toggles.length) {
    toggles.forEach((btn) => {
      const activate = () => {
        const target = btn.dataset.stageTarget;
        stage.dataset.active = target;
        toggles.forEach((x) => x.setAttribute('aria-pressed', String(x === btn)));
      };
      btn.addEventListener('mouseenter', activate);
      btn.addEventListener('focus', activate);
      btn.addEventListener('click', activate);
    });
  }

  // Route transition — visual continuity without slowing navigation.
  document.querySelectorAll('a[href]').forEach((link) => {
    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('https://t.me') || link.target === '_blank') return;
    link.addEventListener('click', (e) => {
      if (reduced || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      document.body.classList.add('page-leaving');
      setTimeout(() => { location.href = href; }, 230);
    });
  });
})();
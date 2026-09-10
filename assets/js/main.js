/* Royal Bliss (Pvt) Ltd — site behaviour */
(function () {
  'use strict';

  /* ---------- Mobile navigation ---------- */
  var toggle = document.querySelector('.nav__toggle');
  var links = document.getElementById('nav-links');

  function isMobile() { return window.matchMedia('(max-width: 900px)').matches; }

  function setNav(open) {
    if (!toggle || !links) return;
    toggle.setAttribute('aria-expanded', String(open));
    links.hidden = !open;
  }

  function syncNav() {
    if (!links) return;
    if (isMobile()) {
      setNav(toggle.getAttribute('aria-expanded') === 'true');
    } else {
      links.hidden = false;
      toggle && toggle.setAttribute('aria-expanded', 'false');
    }
  }

  if (toggle && links) {
    setNav(false);
    syncNav();
    toggle.addEventListener('click', function () {
      setNav(toggle.getAttribute('aria-expanded') !== 'true');
    });
    links.addEventListener('click', function (e) {
      if (e.target.tagName === 'A' && isMobile()) setNav(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && isMobile()) setNav(false);
    });
    window.addEventListener('resize', syncNav);
  }

  /* ---------- Current year in footer ---------- */
  Array.prototype.forEach.call(document.querySelectorAll('[data-year]'), function (el) {
    el.textContent = String(new Date().getFullYear());
  });

  /* ---------- Scroll reveal ---------- */
  var revealables = document.querySelectorAll('.reveal');
  if (revealables.length) {
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            io.unobserve(entry.target);
          }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
      Array.prototype.forEach.call(revealables, function (el) { io.observe(el); });
    } else {
      Array.prototype.forEach.call(revealables, function (el) { el.classList.add('is-visible'); });
    }
  }

  /* ---------- Forms ----------
     Set data-endpoint on the <form> to a form-handling URL (Formspree,
     Getform, Basin, …) to receive submissions. With no endpoint the form
     falls back to opening the visitor's email client.
  ------------------------------------------------------------------ */
  Array.prototype.forEach.call(document.querySelectorAll('form[data-form]'), function (form) {
    var status = form.querySelector('.form__status');
    var submit = form.querySelector('button[type="submit"]');

    function say(message, ok) {
      if (!status) return;
      status.hidden = false;
      status.textContent = message;
      status.className = 'form__status ' + (ok ? 'form__status--ok' : 'form__status--err');
    }

    form.addEventListener('submit', function (e) {
      var endpoint = form.getAttribute('data-endpoint');
      var data = new FormData(form);

      /* Honeypot: silently drop bot submissions. */
      if (data.get('company_website')) { e.preventDefault(); return; }

      if (!endpoint) {
        e.preventDefault();
        var to = form.getAttribute('data-mailto') || 'hello@royalbliss.lk';
        var subject = form.getAttribute('data-subject') || 'Website enquiry';
        var body = [];
        data.forEach(function (value, key) {
          if (key === 'company_website' || !String(value).trim()) return;
          body.push(key.replace(/_/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); }) + ': ' + value);
        });
        window.location.href = 'mailto:' + to +
          '?subject=' + encodeURIComponent(subject) +
          '&body=' + encodeURIComponent(body.join('\n'));
        say('Opening your email app so you can send this enquiry to ' + to + '.', true);
        return;
      }

      e.preventDefault();
      if (submit) { submit.disabled = true; submit.dataset.label = submit.textContent; submit.textContent = 'Sending…'; }

      fetch(endpoint, { method: 'POST', body: data, headers: { Accept: 'application/json' } })
        .then(function (res) {
          if (!res.ok) throw new Error('Request failed');
          form.reset();
          say('Thank you — your enquiry has been received. Our team will be in touch within two business days.', true);
        })
        .catch(function () {
          say('Sorry, something went wrong. Please email us directly at ' + (form.getAttribute('data-mailto') || 'hello@royalbliss.lk') + '.', false);
        })
        .then(function () {
          if (submit) { submit.disabled = false; submit.textContent = submit.dataset.label || 'Send'; }
        });
    });
  });
})();

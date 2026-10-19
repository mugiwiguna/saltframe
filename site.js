/* Saltframe shared: nav, reveal, parallax, lightbox, heading jumps. */
const $ = s => document.querySelector(s);

const burger = $('#burger'), rail = $('.rail');
if (burger && rail) {
  burger.addEventListener('click', () => rail.classList.toggle('open'));
}

/* scroll rule */
const rl = document.querySelector('.rule');
if (rl) addEventListener('scroll', () => rl.classList.toggle('on', scrollY > 60), { passive: true });

/* reveal + gentle parallax */
const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('show'); io.unobserve(e.target); } }), { threshold: .12 });
document.querySelectorAll('.rv').forEach((el, i) => { el.style.transitionDelay = (i % 4 * .07) + 's'; io.observe(el); });
const matImg = document.getElementById('matImg');
if (matImg) addEventListener('scroll', () => {
  const r = matImg.parentElement.getBoundingClientRect();
  if (r.top < innerHeight && r.bottom > 0) matImg.style.transform = `translateY(${(r.top - innerHeight / 2) * .07}px) scale(1.06)`;
}, { passive: true });

/* lightbox: any [data-lb] image or commission photo */
const lb = $('#lb'), lbImg = $('#lbImg'), lbCap = $('#lbCap');
function openLb(src, cap) { lbImg.src = src; lbCap.textContent = cap || ''; lb.classList.add('open'); document.body.style.overflow = 'hidden'; }
function closeLb() { lb.classList.remove('open'); document.body.style.overflow = ''; }
if (lb) {
  lb.addEventListener('click', closeLb);
  addEventListener('keydown', e => { if (e.key === 'Escape') closeLb(); });
}
document.addEventListener('click', e => {
  const img = e.target.closest('[data-lb],.comm img');
  if (img && !lb.contains(img)) { e.preventDefault(); openLb(img.dataset.lb || img.src, img.dataset.cap || img.alt); return; }
  const h = e.target.closest('[data-goto]');
  if (h) document.querySelector(h.dataset.goto)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

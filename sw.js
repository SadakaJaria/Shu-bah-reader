/* عامل الخدمة: يجعل التطبيق يفتح دون إنترنت ويُثبَّت من كروم.

   الهيكل (الصفحة والبيانات والخطوط) يُخزَّن عند التثبيت.
   صفحات المصحف ٦٥ ميغا فلا تُخزَّن دفعةً واحدة: كلّ صفحة تُقرأ تُحفظ،
   فيصير ما قرأه متاحاً دون إنترنت من غير أن نُثقل الجهاز من أوّل يوم. */

const SHELL = 'shubah-shell-v2';
const PAGES = 'shubah-pages-v1';

const SHELL_FILES = [
  './',
  './index.html',
  './quran-shubah.json',
  './manifest.json',
  './fonts/lateef-arabic-400.woff2',
  './fonts/ibm-plex-sans-arabic-400.woff2',
  './fonts/ibm-plex-sans-arabic-700.woff2',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(SHELL)
      // addAll يفشل كلّه لو فشل ملفّ واحد؛ نضيف كلاً على حدة
      .then(c => Promise.allSettled(SHELL_FILES.map(f => c.add(f))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== SHELL && k !== PAGES).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if(req.method !== 'GET') return;
  const url = new URL(req.url);
  if(url.origin !== self.location.origin) return;

  // صفحات المصحف: من المخزن أوّلاً ثمّ الشبكة، وتُحفظ عند أوّل قراءة
  if(url.pathname.includes('/pages/')){
    e.respondWith(
      caches.open(PAGES).then(c =>
        c.match(req).then(hit => hit || fetch(req).then(res => {
          if(res.ok) c.put(req, res.clone());
          return res;
        }))
      )
    );
    return;
  }

  // صفحة التطبيق: من الشبكة أوّلاً والمخزن احتياطاً.
  // «المخزن أوّلاً» كان يُبقي المستخدم على نسخةٍ قديمة حتى يفتح التطبيق
  // مرّتين — يرى تحديث اليوم غداً. الفارق في الشبكة ملفٌّ واحد صغير.
  if(req.mode === 'navigate' || url.pathname.endsWith('.html') || url.pathname === '/'){
    e.respondWith(
      fetch(req).then(res => {
        if(res.ok) caches.open(SHELL).then(c => c.put(req, res.clone()));
        return res;
      }).catch(() => caches.match(req).then(hit => hit || caches.match('./index.html')))
    );
    return;
  }

  // البقية (خطوط وبيانات وأيقونات): من المخزن أوّلاً وتُحدَّث في الخلفية
  e.respondWith(
    caches.match(req).then(hit => {
      const net = fetch(req).then(res => {
        if(res.ok) caches.open(SHELL).then(c => c.put(req, res.clone()));
        return res;
      }).catch(() => hit);
      return hit || net;
    })
  );
});

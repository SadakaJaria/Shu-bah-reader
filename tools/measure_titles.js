const {chromium}=require('playwright'); const fs=require('fs');
(async()=>{
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const pg=await b.newPage({viewport:{width:412,height:1400},deviceScaleFactor:1});
  await pg.goto('http://127.0.0.1:8095/index.html',{waitUntil:'networkidle'});
  await pg.waitForTimeout(1500);
  const pages = await pg.evaluate(()=>{const o=new Set();
    for(const [p,ay] of PAGES) if(ay.some(a=>a.aya===1)) o.add(p);
    return [...o].sort((a,b)=>a-b);});
  fs.mkdirSync('m',{recursive:true});
  const out=[];
  for(const n of pages){
    await pg.evaluate(x=>goto(x), n); await pg.waitForTimeout(430);
    const info = await pg.evaluate(()=>{
      const svg=pageEl.querySelector('svg'), sr=svg.getBoundingClientRect();
      const ctm=svg.getScreenCTM(), inv=ctm.inverse();
      const st=[...pageEl.querySelectorAll('.stitle')].map(e=>{const q=e.getBoundingClientRect();
        return {top:q.top-sr.top, bot:q.bottom-sr.top};});
      pageEl.querySelectorAll('.stitle').forEach(e=>e.style.visibility='hidden');
      // معامل التحويل: بكسل داخل الصندوق → إحداثيّ viewBox
      const a=new DOMPoint(sr.x, sr.y).matrixTransform(inv);
      const c=new DOMPoint(sr.x, sr.y+100).matrixTransform(inv);
      return {st, box:{x:sr.x,y:sr.y,width:sr.width,height:sr.height},
              y0:a.y, per:(c.y-a.y)/100,
              suras:(PAGES.get(current)||[]).filter(v=>v.aya===1).map(v=>v.sura)};
    });
    await pg.screenshot({path:`m/${n}.png`, clip:info.box});
    await pg.evaluate(()=>pageEl.querySelectorAll('.stitle').forEach(e=>e.style.visibility=''));
    out.push({n, ...info});
  }
  fs.writeFileSync('m/meta.json', JSON.stringify(out));
  console.log('قِيست', out.length, 'صفحة');
  await b.close();
})();

/*  كيف يُعاد التوليد:
      python3 serve.py 8095 &
      NODE_PATH=/opt/node22/lib/node_modules node tools/measure_titles.js
    ثمّ تُمسح صفوف الحبر من الصور وتُحوَّل إلى إحداثيّات viewBox، فيخرج
    جدول TITLE_INK الذي في index.html. قِيس مرّةً وثُبِّت: الصفحات لا
    تتغيّر، فلا داعي لقياسه في كلّ فتحة.                                   */

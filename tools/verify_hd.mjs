// Diagnóstico HD: carga, render, clips resueltos, arma en RightHand, anim, perf.
// Uso: node tools/verify_hd.mjs  (requiere python -m http.server 8123 en la raíz)
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const OUT = path.resolve('tools/shots'); fs.mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ executablePath: CHROME, headless: true,
  args: ['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--autoplay-policy=no-user-gesture-required'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const errors = [];
page.on('console', m => { if (m.type()==='error') { errors.push(m.text()); console.log('[cerr]', m.text()); } });
page.on('pageerror', e => { errors.push('PAGEERROR: '+e.message); console.log('[pageerror]', e.message); });
const waitCond = (fn, t=60000) => page.waitForFunction(fn, null, { timeout: t, polling: 250 });

await page.goto('http://localhost:8123/index.html?debug=1', { waitUntil: 'load', timeout: 60000 });
await waitCond(() => window.__game && window.__game.state.matchState==='FIGHT');
console.log('FIGHT reached');
// Esperar a que AMBOS luchadores sean HD (carga async de los GLB)
await waitCond(() => { const g=window.__game; return g.p1.mesh.userData.hd===true && g.p2.mesh.userData.hd===true; });
console.log('both HD loaded');
await page.evaluate(() => { window.__game.setAuto(false); window.__game.freezeAI(true); });

const info = await page.evaluate(() => {
  const g=window.__game;
  const clips = m => Object.entries(m.userData.hdClips||{}).filter(([k,v])=>v).map(([k])=>k);
  const hand = m => { let n=null; m.traverse(o=>{ if(!n && /righthand/i.test(o.name||'')) n=o.name; }); return n; };
  return {
    p1kind:g.p1.kind, p2kind:g.p2.kind,
    p1clips:clips(g.p1.mesh), p2clips:clips(g.p2.mesh),
    p1hand:hand(g.p1.mesh), p2hand:hand(g.p2.mesh),
    p1animCur:g.p1.mesh.userData.animCur?.getClip()?.name||null,
    tris:g.renderer.info.render.triangles, calls:g.renderer.info.render.calls,
    mixers:g.state.mixers,
  };
});
console.log('HD info:', JSON.stringify(info, null, 1));
const layout = await page.evaluate(() => {
  const r = s => { const e=document.querySelector(s); if(!e) return null; const b=e.getBoundingClientRect(); return {t:Math.round(b.top),b:Math.round(b.bottom),l:Math.round(b.left),r:Math.round(b.right)}; };
  const hudL=r('.hud .card'), top=r('.topbtns'), wb=r('.weaponbar');
  const overlap=(a,c)=> a&&c && a.t < c.b && c.t < a.b;
  return { hudL, top, wb,
    hudTopOverlap: overlap(hudL,top), topWbOverlap: overlap(top,wb),
    scrollW: document.documentElement.scrollWidth, innerW: innerWidth,
    topUIh: Math.round(document.getElementById('topUI').getBoundingClientRect().height) };
});
console.log('layout:', JSON.stringify(layout));
await page.screenshot({ path: path.join(OUT, 'hd_idle.png') });

// Arma: espada debe anclarse al hueso RightHand
await page.evaluate(() => window.__game.setWeapon('sword'));
await page.waitForTimeout(400);
const wpn = await page.evaluate(() => {
  const g=window.__game;
  const wm=g.p1.weaponMesh;
  return { hasWeapon:!!wm, parent: wm&&wm.parent? wm.parent.name : null,
           parentIsHand: !!(wm&&wm.parent&&/righthand/i.test(wm.parent.name||'')) };
});
console.log('weapon attach:', JSON.stringify(wpn));

// Anim de ataque: punch debe reproducir un clip one-shot
await page.evaluate(() => { const g=window.__game; g.clean(); g.teleport('p1',1,0); g.teleport('p2',2.4,0); });
await page.evaluate(() => window.__game.attack('p1','punch'));
await page.waitForTimeout(300);
const atkAnim = await page.evaluate(() => window.__game.p1.mesh.userData.animCur?.getClip()?.name||null);
console.log('attack anim clip:', atkAnim);
await page.screenshot({ path: path.join(OUT, 'hd_attack.png') });

// Movimiento: walk/run clip
await page.evaluate(() => { const g=window.__game; g.clean(); g.p1._speed=5; });
await page.waitForTimeout(250);
const runAnim = await page.evaluate(() => window.__game.p1.mesh.userData.animCur?.getClip()?.name||null);
console.log('run anim clip (speed=5):', runAnim);

console.log('console errors:', errors.length ? errors : 'none');
await browser.close();
const fatal = errors.filter(e => !/Failed to load resource|404|net::|favicon|GLTFLoader.*assets\/models\/(titan|soldier|volt|ninja|samurai|gladiator|brute|vamp|ronin|rhino|panda|roja|ogro)/.test(e));
let fail=false;
if (fatal.length){ console.error('FATAL:', fatal); fail=true; }
if (info.p1kind!=='hd_ninja'||info.p2kind!=='hd_soldier'){ console.error('FAIL: kinds no HD'); fail=true; }
if (!info.p1clips.includes('Idle')){ console.error('FAIL: sin clip Idle'); fail=true; }
if (!info.p1hand){ console.error('FAIL: sin hueso RightHand'); fail=true; }
if (!wpn.parentIsHand){ console.error('FAIL: arma no anclada a RightHand:', wpn.parent); fail=true; }
if (layout.hudTopOverlap || layout.topWbOverlap){ console.error('FAIL: solapamiento filas superiores'); fail=true; }
if (layout.scrollW > layout.innerW){ console.error('FAIL: overflow horizontal', layout.scrollW, layout.innerW); fail=true; }
console.log(fail ? 'HD_VERIFY_FAIL' : 'HD_VERIFY_OK');
process.exit(fail?1:0);
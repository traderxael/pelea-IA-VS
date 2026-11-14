// E2E completo: desktop 1280x720, movil 390x844 hasTouch, file:// fallback.
// Chrome real headless + swiftshader (~3-4 FPS): TODOS los waits por condicion de estado.
// Uso: node tools/e2e.mjs   (requiere python -m http.server 8123 en la raiz)
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const ROOT = path.resolve('.');
const OUT = path.resolve('tools/shots'); fs.mkdirSync(OUT, { recursive: true });
const HTTP = 'http://localhost:8123/index.html?debug=1';
const FILE = 'file://' + ROOT.replace(/\\/g, '/') + '/index.html?debug=1';
const FULL_CLIPS = ['Idle','Walk','Run','KO','Punch1','Punch2','Kick','Uppercut','Hammer_Overhead','SwordAttack','Special_Cast','HitHigh','HitLow','Block','Knockdown','Getup','Victory','JumpStart','JumpLoop','JumpLand','Roll'];

const browser = await chromium.launch({ executablePath: CHROME, headless: true,
  args: ['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--autoplay-policy=no-user-gesture-required'] });
let fail = false;
const bad = (msg) => { console.error('FAIL:', msg); fail = true; };
const mkPage = async (opts) => {
  const page = await browser.newPage(opts);
  const errors = [];
  page.on('console', m => { if (m.type()==='error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR: '+e.message));
  page._errors = errors;
  return page;
};
const fatalOf = (errs) => errs.filter(e => !/Failed to load resource|404|net::|favicon|ERR_FILE_NOT_FOUND|GLTFLoader|assets\/models/.test(e));
const waitCond = (page, fn, t=60000) => page.waitForFunction(fn, null, { timeout: t, polling: 200 });
const waitFight = (page) => waitCond(page, () => window.__game && window.__game.state.matchState==='FIGHT');

// ── DESKTOP ────────────────────────────────────────────────────────────────
console.log('== DESKTOP 1280x720 ==');
{
  const page = await mkPage({ viewport: { width: 1280, height: 720 } });
  const glbStatus = [];
  page.on('response', r => { if (/hd_.*\.glb/.test(r.url())) glbStatus.push(r.status()); });
  await page.goto(HTTP, { waitUntil: 'load', timeout: 60000 });
  await waitFight(page);
  await waitCond(page, () => window.__game.p1.mesh.userData.hd===true && window.__game.p2.mesh.userData.hd===true);
  if (!glbStatus.length || glbStatus.some(s => s!==200)) bad('GLB hd no 200: '+glbStatus);
  await page.evaluate(() => { window.__game.setAuto(false); window.__game.freezeAI(true); });

  const clips = await page.evaluate(() => Object.entries(window.__game.p1.mesh.userData.hdClips||{}).filter(([k,v])=>v).map(([k])=>k));
  const missing = FULL_CLIPS.filter(c => !clips.includes(c));
  console.log('clips resueltos:', clips.length, missing.length ? ('| pending F1: '+missing.join(',')) : '| CLIPS_COMPLETE');

  const layout = await page.evaluate(() => {
    const r = s => { const b=document.querySelector(s).getBoundingClientRect(); return {t:b.top,b:b.bottom}; };
    const ov=(a,c)=>a.t<c.b&&c.t<a.b;
    return { ov1: ov(r('.hud .card'), r('.topbtns')), ov2: ov(r('.topbtns'), r('.weaponbar')),
             scrollW: document.documentElement.scrollWidth, innerW: innerWidth };
  });
  if (layout.ov1 || layout.ov2) bad('solapamiento HUD desktop');
  if (layout.scrollW > layout.innerW) bad('overflow horizontal desktop');

  // puno dana
  await page.evaluate(() => { const g=window.__game; g.clean(); g.teleport('p1',1,0); g.teleport('p2',2.4,0); g.p2.blocking=false; });
  const hpB = await page.evaluate(() => window.__game.state.p2.hp);
  await page.evaluate(() => window.__game.attack('p1','punch'));
  await page.waitForFunction(t => window.__game.state.p2.hp < t, hpB, { timeout: 45000, polling: 200 }).catch(()=>bad('punch no dono (timeout)'));
  const hpA = await page.evaluate(() => window.__game.state.p2.hp);
  if (hpA >= hpB) bad('punch no bajo hp');
  console.log(`punch hp ${hpB}->${hpA}`);
  await waitCond(page, () => { const s=window.__game.state; return !s.p1.move && s.p1.knockdown<=0; });

  // bloqueo chip determinista
  await page.evaluate(() => { const g=window.__game; g.clean(); g.teleport('p1',1,0); g.teleport('p2',2.4,0); g.p2.blocking=true; });
  const cB = await page.evaluate(() => window.__game.state.p2.hp);
  await page.evaluate(() => window.__game.attack('p1','kick'));
  await page.waitForFunction(t => window.__game.state.p2.hp < t, cB, { timeout: 45000, polling: 200 });
  const cA = await page.evaluate(() => window.__game.state.p2.hp);
  const chip = cB - cA;
  if (!(chip>0 && chip<=5)) bad('chip incorrecto: '+chip);
  console.log('chip delta', chip);
  await page.evaluate(() => { window.__game.p2.blocking=false; window.__game.clean(); });

  // salto
  await page.evaluate(() => window.__game.jump());
  await waitCond(page, () => window.__game.state.p1.y > 0.5);
  await waitCond(page, () => !window.__game.state.p1.jump);
  console.log('salto ok');

  // arma en RightHand
  await page.evaluate(() => window.__game.setWeapon('sword'));
  const hand = await page.evaluate(() => { const wm=window.__game.p1.weaponMesh; return wm&&wm.parent? wm.parent.name : null; });
  if (!/righthand/i.test(hand||'')) bad('arma no en RightHand: '+hand);
  await page.evaluate(() => window.__game.setWeapon('fists'));

  // AUTO: ambos hp bajan en ~10s de juego
  await page.evaluate(() => { window.__game.freezeAI(false); window.__game.setAuto(true); window.__game.startMatch(); });
  await waitFight(page);
  const aB = await page.evaluate(() => [window.__game.state.p1.hp, window.__game.state.p2.hp]);
  await page.waitForFunction(([h1,h2]) => { const s=window.__game.state; return s.p1.hp<h1 || s.p2.hp<h2; }, aB, { timeout: 60000, polling: 300 }).catch(()=>bad('AUTO no dono'));
  const aA = await page.evaluate(() => [window.__game.state.p1.hp, window.__game.state.p2.hp]);
  if (!(aA[0]<aB[0] || aA[1]<aB[1])) bad('AUTO: nadie dono');
  console.log('AUTO hp', aB, '->', aA);
  await page.evaluate(() => { window.__game.setAuto(false); window.__game.freezeAI(true); });

  // best-of-3 -> FINISH -> JKL -> FATALITY -> rematch
  await page.evaluate(() => window.__game.startMatch());
  await waitFight(page);
  await page.evaluate(() => { window.__game.setAuto(false); window.__game.freezeAI(true); });
  await page.evaluate(() => window.__game.forceKO('p2'));
  await waitCond(page, () => window.__game.state.roundNum===2 && window.__game.state.matchState==='FIGHT');
  await page.evaluate(() => window.__game.forceKO('p2'));
  await waitCond(page, () => window.__game.state.matchState==='FINISH');
  await page.screenshot({ path: path.join(OUT, 'e2e_finish.png') });
  await page.evaluate(() => { window.__game.finishInput('j'); window.__game.finishInput('k'); window.__game.finishInput('l'); });
  await waitCond(page, () => window.__game.state.matchState==='MATCH_END');
  const fat = await page.evaluate(() => document.getElementById('victoryFatality').classList.contains('on'));
  if (!fat) bad('fatality banner off');
  await page.screenshot({ path: path.join(OUT, 'e2e_victory.png') });
  const mixB = await page.evaluate(() => window.__game.state.mixers);
  await page.evaluate(() => document.getElementById('rematchBtn').click());
  await waitFight(page);
  const after = await page.evaluate(() => window.__game.state);
  if (after.wins1!==0 || after.wins2!==0) bad('rematch no resetea wins');
  if (after.mixers > mixB) bad('leak mixers: '+mixB+'->'+after.mixers);
  console.log('rematch ok, mixers', mixB, '->', after.mixers);

  // legacy swap sigue funcionando
  await page.evaluate(() => { document.getElementById('charSel').value='ronin'; document.getElementById('charSel').dispatchEvent(new Event('change')); });
  await waitCond(page, () => window.__game.state.p1.kind==='ronin');
  console.log('legacy swap ok');

  const info = await page.evaluate(() => ({ tris: window.__game.renderer.info.render.triangles, calls: window.__game.renderer.info.render.calls }));
  if (info.tris>=120000) bad('tris fuera de presupuesto: '+info.tris);
  if (info.calls>=150) bad('calls fuera de presupuesto: '+info.calls);
  // FPS referencia swiftshader
  const f0 = await page.evaluate(() => window.__game.renderer.info.render.frame);
  await page.waitForTimeout(3000);
  const f1 = await page.evaluate(() => window.__game.renderer.info.render.frame);
  console.log('renderer.info', JSON.stringify(info), '| FPS(swiftshader ref)', ((f1-f0)/3).toFixed(1));
  const fe = fatalOf(page._errors);
  if (fe.length) bad('desktop console fatal: '+fe.join(' | '));
  console.log('desktop console errors(no fatales):', page._errors.length);
  await page.close();
}

// ── MOVIL ──────────────────────────────────────────────────────────────────
console.log('== MOVIL 390x844 hasTouch ==');
{
  const page = await mkPage({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  await page.goto(HTTP, { waitUntil: 'load', timeout: 60000 });
  await waitFight(page);
  await waitCond(page, () => window.__game.p1.mesh.userData.hd===true);
  await page.evaluate(() => { window.__game.setAuto(false); window.__game.freezeAI(true); window.__game.clean(); });
  const cdp = await page.context().newCDPSession(page);
  const joy = await page.evaluate(() => { const b=document.getElementById('joyBase').getBoundingClientRect(); return { x:b.left+b.width/2, y:b.top+b.height/2 }; });
  const x0 = await page.evaluate(() => window.__game.state.p1.x);
  await cdp.send('Input.dispatchTouchEvent', { type:'touchStart', touchPoints:[{ x:joy.x, y:joy.y, id:1 }] });
  await cdp.send('Input.dispatchTouchEvent', { type:'touchMove', touchPoints:[{ x:joy.x+40, y:joy.y, id:1 }] });
  await page.waitForFunction(x => window.__game.state.p1.x > x + 0.3, x0, { timeout: 30000, polling: 200 }).catch(()=>bad('joystick no mueve'));
  await cdp.send('Input.dispatchTouchEvent', { type:'touchEnd', touchPoints:[] });
  const x1 = await page.evaluate(() => window.__game.state.p1.x);
  if (x1 <= x0) bad('joystick no desplazo p1');
  console.log('joystick x', x0.toFixed(2), '->', x1.toFixed(2));

  // bloqueo hold tactil
  const bb = await page.evaluate(() => { const b=document.getElementById('block').getBoundingClientRect(); return { x:b.left+b.width/2, y:b.top+b.height/2 }; });
  await cdp.send('Input.dispatchTouchEvent', { type:'touchStart', touchPoints:[{ x:bb.x, y:bb.y, id:2 }] });
  await waitCond(page, () => window.__game.state.p1.blocking===true);
  await cdp.send('Input.dispatchTouchEvent', { type:'touchEnd', touchPoints:[] });
  await waitCond(page, () => window.__game.state.p1.blocking===false);
  console.log('block hold ok');

  // doble-tap puno = launcher: taps sincronos en-page (gap<280ms fiable; CDP async se separa >280ms a 2-4 FPS).
  // Se lee move inmediatamente tras los taps: 'launcher' dura .62s y se perderia entre polls.
  const dbl = await page.evaluate(() => {
    const g=window.__game; g.clean();
    const el=document.getElementById('punch');
    const tap=()=>el.dispatchEvent(new TouchEvent('touchstart',{bubbles:true,cancelable:true}));
    tap(); tap();
    return { move:g.state.p1.move, moveName:g.state.p1.moveName };
  });
  if (dbl.move!=='launcher' && dbl.moveName!=='launcher') bad('dbltap no launcher: '+JSON.stringify(dbl));
  else console.log('dbltap launcher ok');

  const ml = await page.evaluate(() => ({ scrollW: document.documentElement.scrollWidth, innerW: innerWidth }));
  if (ml.scrollW > ml.innerW) bad('overflow horizontal movil');
  await page.screenshot({ path: path.join(OUT, 'e2e_mobile.png') });
  const fe = fatalOf(page._errors);
  if (fe.length) bad('movil console fatal: '+fe.join(' | '));
  await page.close();
}

// ── FILE:// ────────────────────────────────────────────────────────────────
console.log('== FILE:// fallback ==');
{
  const page = await mkPage({ viewport: { width: 960, height: 540 } });
  await page.goto(FILE, { waitUntil: 'load', timeout: 60000 });
  await waitFight(page);
  const st = await page.evaluate(() => ({ hd: window.__game.p1.mesh.userData.hd===true, kind: window.__game.state.p1.kind, isGltf: window.__game.p1.mesh.userData.isGltf===true }));
  if (st.hd) bad('file:// no deberia cargar HD');
  console.log('file:// fallback:', JSON.stringify(st));
  await page.screenshot({ path: path.join(OUT, 'e2e_file.png') });
  const fe = fatalOf(page._errors);
  if (fe.length) bad('file:// console fatal: '+fe.join(' | '));
  await page.close();
}

await browser.close();
console.log(fail ? 'E2E_FAIL' : 'E2E_OK');
process.exit(fail?1:0);
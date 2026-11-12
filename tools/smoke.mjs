// Smoke test: carga, combate MK, bloqueo chip, salto, best-of-3, FINISH HIM, fatality, rematch.
// Swiftshader corre a ~3 FPS: TODOS los waits son por condición de estado (tiempo de juego), no sleeps.
// Uso: node tools/smoke.mjs  (requiere python -m http.server 8123 en la raíz)
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://localhost:8123/index.html?debug=1';
const OUT = path.resolve('tools/shots');
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'],
});
const page = await browser.newPage({ viewport: { width: 960, height: 540 } });
const errors = [];
page.on('console', m => { if (m.type() === 'error') { errors.push(m.text()); console.log('[console.error]', m.text()); } });
page.on('pageerror', e => { errors.push('PAGEERROR: ' + e.message); console.log('[pageerror]', e.message); });

const st = () => page.evaluate(() => window.__game.state);
const waitCond = (fn, timeout = 45000) => page.waitForFunction(fn, null, { timeout, polling: 200 });
const waitFight = () => waitCond(() => window.__game.state.matchState === 'FIGHT');
const idleP1 = () => waitCond(() => { const s = window.__game.state; return !s.p1.move && s.matchState === 'FIGHT' && s.p1.knockdown <= 0; });

await page.goto(URL, { waitUntil: 'load', timeout: 60000 });
await waitFight();
console.log('FIGHT reached');
await page.evaluate(() => { window.__game.setAuto(false); window.__game.freezeAI(true); });
await idleP1();

// punch conecta (ventana activa en el loop)
await page.evaluate(() => {
  const g = window.__game;
  g.clean();
  g.teleport('p1', 1.0, 0); g.teleport('p2', 2.4, 0);
});
const hpBefore = await page.evaluate(() => window.__game.state.p2.hp);
await page.evaluate(() => window.__game.attack('p1', 'punch'));
await page.waitForFunction(t => window.__game.state.p2.hp < t, hpBefore, { timeout: 45000, polling: 200 });
const hpAfter = await page.evaluate(() => window.__game.state.p2.hp);
console.log(`punch: p2 hp ${hpBefore} -> ${hpAfter}`);
await idleP1();

// bloqueo: chip determinista ~20% (kick 13 → chip 3)
await page.evaluate(() => {
  const g = window.__game;
  g.clean();
  g.teleport('p1', 1.0, 0); g.teleport('p2', 2.4, 0);
  g.p2.blocking = true;
});
const hpB = await page.evaluate(() => window.__game.state.p2.hp);
await page.evaluate(() => window.__game.attack('p1', 'kick'));
await page.waitForFunction(t => window.__game.state.p2.hp < t, hpB, { timeout: 45000, polling: 200 });
const hpA = await page.evaluate(() => window.__game.state.p2.hp);
console.log(`block chip: p2 hp ${hpB} -> ${hpA} (delta ${hpB - hpA})`);
await idleP1();

// salto del jugador
await page.evaluate(() => { window.__game.p2.blocking = false; window.__game.jump(); });
await waitCond(() => window.__game.state.p1.y > 0.5);
const jy = await page.evaluate(() => window.__game.state.p1.y);
console.log(`jump: p1.y=${jy.toFixed(2)}`);
await waitCond(() => !window.__game.state.p1.jump);

// best-of-3 → FINISH HIM en match point → J,K,L → FATALITY
await page.evaluate(() => window.__game.startMatch());
await waitFight();
await page.evaluate(() => { window.__game.setAuto(false); window.__game.freezeAI(true); });
await page.evaluate(() => window.__game.forceKO('p2'));
await waitCond(() => window.__game.state.roundNum === 2 && window.__game.state.matchState === 'FIGHT');
await page.evaluate(() => window.__game.forceKO('p2'));
await waitCond(() => window.__game.state.matchState === 'FINISH');
console.log('FINISH HIM reached, wins1:', (await st()).wins1);
await page.screenshot({ path: path.join(OUT, 'finish.png') });
await page.evaluate(() => { window.__game.finishInput('j'); window.__game.finishInput('k'); window.__game.finishInput('l'); });
await waitCond(() => window.__game.state.matchState === 'MATCH_END');
const fatalityOn = await page.evaluate(() => document.getElementById('victoryFatality').classList.contains('on'));
console.log('MATCH_END, fatality banner:', fatalityOn);
await page.screenshot({ path: path.join(OUT, 'victory.png') });

// rematch resetea wins y no deja mixers huérfanos
const mixersBefore = (await st()).mixers;
await page.evaluate(() => document.getElementById('rematchBtn').click());
await waitFight();
const after = await st();
console.log('rematch:', JSON.stringify({ wins1: after.wins1, wins2: after.wins2, round: after.roundNum, hp1: after.p1.hp, mixers: after.mixers, mixersBefore }));

const info = await page.evaluate(() => ({ calls: window.__game.renderer.info.render.calls, tris: window.__game.renderer.info.render.triangles }));
console.log('renderer.info:', JSON.stringify(info));
console.log('console errors:', errors.length ? errors : 'none');
await browser.close();
const fatal = errors.filter(e => !/Failed to load resource|404|net::|GLTFLoader|assets\/models|favicon/.test(e));
let fail = false;
if (fatal.length) { console.error('FATAL ERRORS:', fatal); fail = true; }
if (hpAfter >= hpBefore) { console.error('FAIL: punch no dañó'); fail = true; }
const chip = hpB - hpA;
if (!(chip > 0 && chip <= 5)) { console.error('FAIL: chip incorrecto:', chip); fail = true; }
if (jy <= 0.5) { console.error('FAIL: salto no subió'); fail = true; }
if (!fatalityOn) { console.error('FAIL: fatality no ejecutada'); fail = true; }
if (after.wins1 !== 0 || after.wins2 !== 0) { console.error('FAIL: rematch no resetea wins'); fail = true; }
console.log(fail ? 'SMOKE_FAIL' : 'SMOKE_OK');
process.exit(fail ? 1 : 0);
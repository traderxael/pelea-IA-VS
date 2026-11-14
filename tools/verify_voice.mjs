// Verifica voces GRATIS (Web Speech) con personalidad distinta por IA + mute.
// Uso: node tools/verify_voice.mjs  (requiere python -m http.server 8123)
import { chromium } from 'playwright-core';
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const browser = await chromium.launch({ executablePath: CHROME, headless: true,
  args: ['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--autoplay-policy=no-user-gesture-required'] });
const page = await browser.newPage({ viewport: { width: 960, height: 540 } });
const errors = [];
page.on('console', m => { if (m.type()==='error') errors.push(m.text()); });
page.on('pageerror', e => errors.push('PAGEERROR: '+e.message));
await page.goto('http://localhost:8123/index.html?debug=1', { waitUntil: 'load', timeout: 60000 });
await page.waitForFunction(() => window.__game && window.__game.state.matchState==='FIGHT', null, { timeout: 60000, polling: 200 });

const hasSpeech = await page.evaluate(() => 'speechSynthesis' in window);
if (!hasSpeech) { console.error('FAIL: sin speechSynthesis'); process.exit(1); }
await page.evaluate(() => {
  window.__spoken = [];
  const orig = speechSynthesis.speak.bind(speechSynthesis);
  speechSynthesis.speak = u => { window.__spoken.push({ text:u.text, pitch:u.pitch, rate:u.rate, voice:u.voice?u.voice.name:null }); return orig(u); };
});
const personas = ['openai','qwen','grok','gemini','deepseek'];
for (const p of personas) {
  await page.evaluate(v => { const s=document.getElementById('personaSel'); s.value=v; s.dispatchEvent(new Event('change')); }, p);
  await page.waitForTimeout(150);
}
const spoken = await page.evaluate(() => window.__spoken);
console.log('voces por persona:', JSON.stringify(spoken, null, 1));
const pitches = spoken.map(s => s.pitch);
const distinct = new Set(pitches.map((p,i)=>p+'/'+spoken[i].rate)).size;
let fail = false;
if (spoken.length < personas.length) { console.error('FAIL: no hablaron todas las personas', spoken.length); fail=true; }
if (distinct < personas.length) { console.error('FAIL: pitch/rate no distintos por persona', distinct); fail=true; }

// mute silencia las voces
await page.evaluate(() => document.getElementById('muteBtn').click());
const before = await page.evaluate(() => window.__spoken.length);
await page.evaluate(() => { const s=document.getElementById('personaSel'); s.value='qwen'; s.dispatchEvent(new Event('change')); });
await page.waitForTimeout(150);
const after = await page.evaluate(() => window.__spoken.length);
if (after !== before) { console.error('FAIL: mute no silencia voces'); fail=true; }
await page.evaluate(() => document.getElementById('muteBtn').click()); // unmute
console.log('mute silencia voces: ok');

const fatal = errors.filter(e => !/Failed to load resource|404|net::|favicon/.test(e));
if (fatal.length) { console.error('FAIL console:', fatal); fail=true; }
console.log('console errors:', errors.length ? errors : 'none');
await browser.close();
console.log(fail ? 'VOICE_FAIL' : 'VOICE_OK');
process.exit(fail?1:0);
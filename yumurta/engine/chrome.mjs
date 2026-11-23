// chrome.mjs — finds a Chrome / Chromium for puppeteer-core. Set CHROME_PATH to use a different browser.
import fs from 'node:fs';
import path from 'node:path';

export function findChrome() {
  if (process.env.CHROME_PATH && !fs.existsSync(process.env.CHROME_PATH)) {
    console.error(`CHROME_PATH bulunamadı / not found: ${process.env.CHROME_PATH}`);
    process.exit(1);
  }
  const local = process.env.LOCALAPPDATA;
  const list = [
    process.env.CHROME_PATH,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    local && path.join(local, 'Google/Chrome/Application/chrome.exe'),
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/snap/bin/chromium',
  ].filter(Boolean);
  const hit = list.find(p => fs.existsSync(p));
  if (!hit) {
    console.error('Chrome bulunamadı / Chrome not found. Kurun ya da yolunu verin / install it or set CHROME_PATH, e.g.\n' +
      '  CHROME_PATH="/path/to/chrome" node render.mjs <story>');
    process.exit(1);
  }
  return hit;
}

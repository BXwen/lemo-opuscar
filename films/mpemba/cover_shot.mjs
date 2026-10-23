// 抖音封面截图：1080×1920 竖版
//   node cover_shot.mjs [output.png]
import { chromium } from 'playwright-core';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
const DIR = path.dirname(fileURLToPath(import.meta.url));
const P = (...a) => path.join(DIR, ...a);
const OUT = path.resolve(process.argv[2] || P('douyin_cover.png'));
const EXE = process.env.CHROME_PATH || process.env.PLAYWRIGHT_CHROME || undefined;

const browser = await chromium.launch({ executablePath: EXE, args: ['--font-render-hinting=none', '--force-color-profile=srgb'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('[pageerror]', e.message));
await page.goto('file://' + P('cover.html'));
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(600);
await page.screenshot({ path: OUT });
await browser.close();
console.log('cover →', OUT);

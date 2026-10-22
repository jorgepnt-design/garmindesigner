// Rendert die Icons (SVG-Quelle) mit Chromium zu PNGs fuer das Zifferblatt.
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const out = process.argv[2];
mkdirSync(out, { recursive: true });
const gold = "#e8cd91";

// Material-Icons (Apache 2.0): wb_sunny, directions_run, alarm
const icons = {
  sun: "M6.76 4.84l-1.8-1.79-1.41 1.41 1.79 1.79 1.42-1.41zM4 10.5H1v2h3v-2zm9-9.95h-2V3.5h2V.55zm7.45 3.91l-1.41-1.41-1.79 1.79 1.41 1.41 1.79-1.79zm-3.21 13.7l1.79 1.8 1.41-1.41-1.8-1.79-1.4 1.4zM20 10.5v2h3v-2h-3zm-8-5c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm-1 16.95h2V19.5h-2v2.95zm-7.45-3.91l1.41 1.41 1.79-1.8-1.41-1.41-1.79 1.8z",
  run: "M13.49 5.48c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm-3.6 13.9l1-4.4 2.1 2v6h2v-7.5l-2.1-2 .6-3c1.3 1.5 3.3 2.5 5.5 2.5v-2c-1.9 0-3.5-1-4.3-2.4l-1-1.6c-.4-.6-1-1-1.7-1-.3 0-.5.1-.8.1l-5.2 2.2v4.7h2v-3.4l1.8-.7-1.6 8.1-4.9-1-.4 2 7 1.4z",
  alarm: "M22 5.72l-4.6-3.86-1.29 1.53 4.6 3.86L22 5.72zM7.88 3.39L6.6 1.86 2 5.71l1.29 1.53 4.59-3.85zM12.5 8H11v6l4.75 2.85.75-1.23-4-2.37V8zM12 4c-4.97 0-9 4.03-9 9s4.02 9 9 9c4.97 0 9-4.03 9-9s-4.03-9-9-9zm0 16c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z",
};

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 1 });

async function render(svg, size, file) {
  await page.setViewportSize({ width: size, height: size });
  await page.setContent(`<html><body style="margin:0;background:#000">${svg}</body></html>`);
  await page.screenshot({ path: file, clip: { x: 0, y: 0, width: size, height: size } });
}

for (const [name, d] of Object.entries(icons)) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="45" height="45" viewBox="0 0 24 24" style="display:block"><path fill="${gold}" d="${d}"/></svg>`;
  await render(svg, 45, `${out}/icon_${name}.png`);
}

// Launcher-Icon: goldenes "E" auf Schwarz
const launcher = `<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 60 60" style="display:block">
  <rect width="60" height="60" fill="#000"/>
  <circle cx="30" cy="30" r="27" fill="none" stroke="${gold}" stroke-width="2"/>
  <text x="30" y="41" text-anchor="middle" font-family="serif" font-size="32" fill="${gold}">E</text></svg>`;
await render(launcher, 60, `${out}/launcher_icon.png`);
await browser.close();

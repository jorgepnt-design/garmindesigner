// Rendert die Icon-Masken (weiss auf transparent, 192 px) aus web/icons.json nach tools/icons/.
// Nur noetig, wenn web/icons.json geaendert wurde: node tools/render_icon_masks.mjs
// Pfade: Material Icons (Apache 2.0)
import { chromium } from "playwright";
import { mkdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, "icons");
mkdirSync(out, { recursive: true });
const icons = JSON.parse(readFileSync(join(here, "..", "web", "icons.json"), "utf8"));

const size = 192;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: size, height: size } });
for (const [name, d] of Object.entries(icons)) {
  await page.setContent(`<html><body style="margin:0;background:transparent">
    <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" style="display:block">
    <path fill="#fff" d="${d}"/></svg></body></html>`);
  await page.screenshot({ path: `${out}/${name}.png`, omitBackground: true });
}
await browser.close();

import { chromium } from "playwright";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

async function main() {
  const args = new Map();
  for (let i = 2; i < process.argv.length; i += 2) {
    args.set(process.argv[i], process.argv[i + 1]);
  }
  const urls = (args.get("--urls") || "").split(",").filter(Boolean);
  const storageState = args.get("--storage");
  const allowExt = (args.get("--allow") || "").split(",").filter(Boolean);

  if (!urls.length || !storageState) {
    console.error("usage: node playwright_discover.mjs --urls url1,url2 --storage path --allow .pdf,.csv");
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    storageState: JSON.parse(await readFile(resolve(storageState), "utf-8")),
  });

  const results = [];
  for (const url of urls) {
    const page = await context.newPage();
    await page.goto(url, { waitUntil: "domcontentloaded" });
    const links = await page.$$eval("a[href]", (anchors) =>
      anchors.map((a) => a.href).filter(Boolean)
    );
    for (const link of links) {
      if (!allowExt.length) {
        results.push(link);
        continue;
      }
      const lower = link.toLowerCase();
      if (allowExt.some((ext) => lower.endsWith(ext))) {
        results.push(link);
      }
    }
    await page.close();
  }
  await browser.close();

  const unique = Array.from(new Set(results));
  process.stdout.write(JSON.stringify(unique));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

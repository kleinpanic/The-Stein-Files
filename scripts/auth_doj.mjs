import { chromium, request } from "playwright";
import { writeFile, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline";
import { spawnSync } from "node:child_process";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const COOKIE_JSON = resolve(ROOT, ".secrets", "justice.gov.cookies.json");
const COOKIE_JAR = resolve(ROOT, ".secrets", "justice.gov.cookies.txt");
const STORAGE_STATE = resolve(ROOT, ".secrets", "doj.storage-state.json");
const PYTHON = resolve(ROOT, ".venv", "bin", "python");
const HUB_URL = "https://www.justice.gov/epstein";

const HUB_TARGETS = {
  disclosures: ["doj disclosures", "disclosures"],
  court_records: ["court records", "court record"],
  foia: ["foia", "freedom of information"],
};

function prompt(message) {
  return new Promise((resolvePrompt) => {
    const rl = createInterface({ input: process.stdin, output: process.stdout });
    rl.question(message, () => {
      rl.close();
      resolvePrompt();
    });
  });
}

function scoreLink(text, href, phrase) {
  const t = text.toLowerCase();
  const h = href.toLowerCase();
  const p = phrase.toLowerCase();
  let score = 0;
  if (t.includes(p)) score += 3;
  if (h.includes(p.replaceAll(" ", "-"))) score += 4;
  if (h.includes(p.replaceAll(" ", ""))) score += 2;
  return score;
}

function pickBest(links, phrases) {
  let best = null;
  let bestScore = 0;
  for (const link of links) {
    const text = `${link.text ?? ""}`.trim();
    const href = `${link.href ?? ""}`.trim();
    if (!href) continue;
    const combined = `${text} ${link.heading ?? ""}`.trim();
    for (const phrase of phrases) {
      const score = scoreLink(combined, href, phrase);
      if (score > bestScore) {
        bestScore = score;
        best = href;
      }
    }
  }
  return best;
}

async function discoverHubTargets(page) {
  await page.goto(HUB_URL, { waitUntil: "domcontentloaded" });
  const links = await page.evaluate(() =>
    Array.from(document.querySelectorAll("a")).map((a) => ({
      href: a.href,
      text: a.textContent || "",
      heading: a.closest("section")?.querySelector("h2, h3")?.textContent || "",
    }))
  );
  const disclosures = pickBest(links, HUB_TARGETS.disclosures);
  const courtRecords = pickBest(links, HUB_TARGETS.court_records);
  const foia = pickBest(links, HUB_TARGETS.foia);
  return {
    disclosures,
    court_records: courtRecords,
    foia,
  };
}

async function main() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  await mkdir(resolve(ROOT, ".secrets"), { recursive: true });

  console.log("[auth] opening DOJ Epstein Library in a real browser...");
  const targets = await discoverHubTargets(page);
  const urls = [HUB_URL];
  for (const [label, url] of Object.entries(targets)) {
    if (!url) {
      console.log(`[auth] not found on hub; skipping navigation for ${label}`);
      continue;
    }
    urls.push(url);
  }
  for (const url of urls) {
    await page.goto(url, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);
  }
  await prompt("[auth] complete any advisory prompts, then press Enter to capture cookies...");

  const cookies = await context.cookies("https://www.justice.gov");
  await writeFile(COOKIE_JSON, JSON.stringify(cookies, null, 2), "utf-8");
  await context.storageState({ path: STORAGE_STATE });

  const pythonExists = existsSync(PYTHON);
  if (!pythonExists) {
    console.error(`[auth] missing ${PYTHON}. Run make setup first.`);
    await browser.close();
    process.exit(1);
  }

  const result = spawnSync(
    PYTHON,
    ["-m", "scripts.cookies", "--input", COOKIE_JSON, "--output", COOKIE_JAR, "--domain", "justice.gov"],
    { stdio: "inherit", cwd: ROOT }
  );
  await browser.close();
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
  const api = await request.newContext({ storageState: STORAGE_STATE });
  let had403 = false;
  for (const url of urls) {
    try {
      const resp = await api.get(url);
      console.log(`[auth] verify ${url} status=${resp.status()}`);
      if (resp.status() === 403) {
        had403 = true;
      }
    } catch (err) {
      console.log(`[auth] verify ${url} status=0`);
      had403 = true;
    }
  }
  await api.dispose();
  if (had403) {
    console.log("[auth] guidance: visit the 403 pages, scroll/ack prompts, then press Enter again.");
  }

  console.log(`[auth] cookie jar written to ${COOKIE_JAR}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

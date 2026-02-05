import { chromium, request } from "playwright";
import { readFile, writeFile, mkdir } from "node:fs/promises";
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
const DOJ_HOST = "https://www.justice.gov";
const CONFIG_PATH = resolve(ROOT, "config", "sources.json");
const SOURCE_IDS = [
  "doj-epstein-hub",
  "doj-epstein-doj-disclosures",
  "doj-epstein-court-records",
  "doj-epstein-foia",
];

function prompt(message) {
  return new Promise((resolvePrompt) => {
    const rl = createInterface({ input: process.stdin, output: process.stdout });
    rl.question(message, () => {
      rl.close();
      resolvePrompt();
    });
  });
}

function normalizeDojUrl(url) {
  if (!url) return url;
  try {
    const parsed = new URL(url);
    if (parsed.host === "justice.gov") {
      parsed.host = "www.justice.gov";
      return parsed.toString();
    }
    if (parsed.host === "www.justice.gov") {
      return parsed.toString();
    }
  } catch (_err) {
    if (url.startsWith("/")) {
      return `${DOJ_HOST}${url}`;
    }
  }
  if (url.startsWith("https://justice.gov/")) {
    return url.replace("https://justice.gov/", `${DOJ_HOST}/`);
  }
  return url;
}

async function loadDojUrls() {
  const raw = await readFile(CONFIG_PATH, "utf-8");
  const config = JSON.parse(raw);
  const sources = config.sources || [];
  const urls = [];
  for (const id of SOURCE_IDS) {
    const source = sources.find((item) => item.id === id);
    if (!source || !source.base_url) {
      throw new Error(`[auth] missing source URL for ${id}`);
    }
    urls.push(normalizeDojUrl(source.base_url));
  }
  return urls;
}

async function isPageNotFound(page) {
  try {
    const heading = await page.textContent("h1");
    return heading && heading.toLowerCase().includes("page not found");
  } catch (_err) {
    return false;
  }
}

async function visitSharePointFrames(page, context) {
  const iframeSrcs = await page.$$eval("iframe", (frames) =>
    frames.map((frame) => frame.getAttribute("src") || "").filter(Boolean)
  );
  const sharepointSrcs = iframeSrcs.filter((src) =>
    src.toLowerCase().includes("sharepoint")
  );
  for (const src of sharepointSrcs) {
    const target = normalizeDojUrl(src);
    const framePage = await context.newPage();
    await framePage.goto(target, { waitUntil: "domcontentloaded" });
    await framePage.waitForTimeout(2000);
    try {
      await framePage.$$eval("a", (anchors) =>
        anchors.slice(0, 3).map((a) => a.href)
      );
    } catch (_err) {
      // ignore anchor extraction errors
    }
    await framePage.close();
  }
}

async function main() {
  const channel = process.env.EPPIE_PLAYWRIGHT_CHANNEL || undefined;
  const browser = await chromium.launch({
    headless: false,
    channel,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  await mkdir(resolve(ROOT, ".secrets"), { recursive: true });

  console.log("[auth] opening DOJ Epstein Library in a real browser...");
  const urls = await loadDojUrls();
  let hadNotFound = false;
  for (const url of urls) {
    await page.goto(url, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);
    if (await isPageNotFound(page)) {
      console.log(`[auth] page not found: ${url}`);
      hadNotFound = true;
      continue;
    }
    await visitSharePointFrames(page, context);
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
  if (hadNotFound) {
    console.log("[auth] warning: one or more URLs returned Page not found");
  }
  if (had403) {
    console.log("[auth] guidance: visit the 403 pages, scroll/ack prompts, then press Enter again.");
  }

  console.log(`[auth] cookie jar written to ${COOKIE_JAR}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

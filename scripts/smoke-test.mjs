import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import http from "node:http";
import { tmpdir } from "node:os";
import path from "node:path";

const chromePath = process.env.CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl = process.env.SMOKE_URL || process.argv[2] || "http://localhost:5174/";
const debugPort = Number(process.env.CHROME_DEBUG_PORT || 9322);
const screenshotPath = process.env.SMOKE_SCREENSHOT || "/private/tmp/first-responsibility-smoke.png";
const userDataDir = path.join(tmpdir(), `first-responsibility-chrome-${Date.now()}`);

await mkdir(userDataDir, { recursive: true });

const chrome = spawn(chromePath, [
  "--headless=new",
  "--disable-gpu",
  "--no-sandbox",
  "--disable-dev-shm-usage",
  `--remote-debugging-port=${debugPort}`,
  `--user-data-dir=${userDataDir}`,
  "--window-size=1440,960",
  "about:blank"
], { stdio: ["ignore", "pipe", "pipe"] });

let ws;
let nextId = 1;
const pending = new Map();
const events = [];

try {
  const tabInfo = await waitForTab(debugPort);
  ws = new WebSocket(tabInfo.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", reject, { once: true });
  });
  ws.addEventListener("message", (event) => {
    const payload = JSON.parse(event.data);
    if (payload.id && pending.has(payload.id)) {
      const { resolve, reject } = pending.get(payload.id);
      pending.delete(payload.id);
      if (payload.error) reject(new Error(payload.error.message));
      else resolve(payload.result);
      return;
    }
    events.push(payload);
  });

  await send("Page.enable");
  await send("Runtime.enable");
  await send("Page.navigate", { url: targetUrl });
  await waitForEvent("Page.loadEventFired", 10000);
  await send("Runtime.evaluate", { expression: "localStorage.clear(); location.reload();", awaitPromise: false });
  await waitForEvent("Page.loadEventFired", 10000);
  await delay(500);

  const initial = await evaluateObject(() => ({
    title: document.title,
    nav: Array.from(document.querySelectorAll(".nav-button")).map((item) => item.textContent.trim()),
    hasComposer: Boolean(document.querySelector(".ask-composer textarea")),
    sendText: document.querySelector(".ask-composer button")?.textContent?.trim() || "",
    activeHeading: document.querySelector(".chat-topbar h1")?.textContent?.trim() || "",
    sidebarWidth: Math.round(document.querySelector(".sidebar")?.getBoundingClientRect().width || 0),
    composerWidth: Math.round(document.querySelector(".ask-composer")?.getBoundingClientRect().width || 0),
    textareaRight: Math.round(document.querySelector(".ask-composer textarea")?.getBoundingClientRect().right || 0),
    sendLeft: Math.round(document.querySelector(".ask-composer button")?.getBoundingClientRect().left || 0),
    sendBg: getComputedStyle(document.querySelector(".ask-composer button")).backgroundColor,
    sendColor: getComputedStyle(document.querySelector(".ask-composer button")).color
  }));

  await send("Runtime.evaluate", {
    expression: `(() => {
      const input = document.querySelector('.ask-composer textarea');
      input.value = '我想申请大模型 Key，应该找谁？';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', bubbles: true }));
    })();`
  });
  await delay(900);

  const afterEnter = await evaluateObject(() => ({
    turns: document.querySelectorAll(".thread-turn").length,
    value: document.querySelector(".ask-composer textarea")?.value || ""
  }));

  await send("Runtime.evaluate", {
    expression: `(() => {
      document.querySelector('.ask-composer button').click();
    })();`
  });
  await delay(900);

  const afterAsk = await evaluateObject(() => ({
    turns: document.querySelectorAll(".thread-turn").length,
    recommendationCards: document.querySelectorAll(".result-card").length,
    firstCard: document.querySelector(".result-card .person-name")?.textContent?.trim() || "",
    hasNoHelpLabel: (document.querySelector(".thread-list")?.textContent || "").includes("没帮助"),
    threadText: document.querySelector(".thread-list")?.textContent?.slice(0, 240) || ""
  }));

  await send("Runtime.evaluate", {
    expression: `document.querySelector('.result-card')?.click();`
  });
  await delay(300);

  const afterPersonCardClick = await evaluateObject(() => ({
    heading: document.querySelector(".chat-topbar h1")?.textContent?.trim() || document.querySelector(".page-heading h1")?.textContent?.trim() || "",
    detailLabel: document.querySelector(".detail-panel-label")?.textContent?.trim() || "",
    detailText: document.querySelector(".detail-panel")?.textContent?.slice(0, 160) || "",
    profilePageVisible: Boolean(document.querySelector(".profile-detail .profile-actions"))
  }));

  await send("Runtime.evaluate", {
    expression: `document.querySelector('.result-card .related-list button')?.click();`
  });
  await delay(300);

  const afterRelatedContentClick = await evaluateObject(() => ({
    heading: document.querySelector(".chat-topbar h1")?.textContent?.trim() || "",
    detailLabel: document.querySelector(".detail-panel-label")?.textContent?.trim() || "",
    detailText: document.querySelector(".detail-panel")?.textContent?.slice(0, 160) || ""
  }));

  await send("Runtime.evaluate", {
    expression: `(() => {
      const clickNewChat = () => Array.from(document.querySelectorAll('button')).find((item) => item.textContent.includes('新对话'))?.click();
      clickNewChat();
      clickNewChat();
    })();`
  });
  await delay(300);

  const afterNewChatTwice = await evaluateObject(() => ({
    historyCards: document.querySelectorAll(".history-card").length,
    emptySessions: Array.from(document.querySelectorAll(".history-card")).filter((item) => item.textContent.includes("空白对话")).length
  }));

  await send("Runtime.evaluate", {
    expression: `Array.from(document.querySelectorAll('.nav-button')).find((item) => item.textContent.includes('名片库'))?.click();`
  });
  await delay(300);

  const directory = await evaluateObject(() => ({
    heading: document.querySelector(".page-heading h1")?.textContent?.trim() || "",
    personCards: document.querySelectorAll(".person-card").length,
    hasElementSelect: Boolean(document.querySelector(".el-select")),
    hasElementInput: Boolean(document.querySelector(".el-input"))
  }));

  await send("Runtime.evaluate", {
    expression: `Array.from(document.querySelectorAll('.nav-button')).find((item) => item.textContent.includes('个人中心'))?.click();`
  });
  await delay(300);

  const mine = await evaluateObject(() => {
    const profile = document.querySelector(".profile-detail");
    const portrait = document.querySelector(".portrait-split-grid");
    return {
      heading: document.querySelector(".page-heading h1")?.textContent?.trim() || "",
      hasProfileDetail: Boolean(profile),
      portraitColumns: portrait ? getComputedStyle(portrait).gridTemplateColumns : "",
      actionText: document.querySelector(".profile-detail .profile-actions")?.textContent?.trim() || "",
      blockCount: document.querySelectorAll(".profile-detail .profile-block").length
    };
  });

  const capture = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  await writeFile(screenshotPath, Buffer.from(capture.data, "base64"));

  const exceptions = events
    .filter((event) => event.method === "Runtime.exceptionThrown")
    .map((event) => event.params?.exceptionDetails?.text || "Runtime exception");

  const result = { targetUrl, screenshotPath, initial, afterEnter, afterAsk, afterPersonCardClick, afterRelatedContentClick, afterNewChatTwice, directory, mine, exceptions };
  const failed = [];
  if (!initial.hasComposer) failed.push("composer missing");
  if (!initial.sendText.includes("发送")) failed.push("send button text missing");
  if (initial.sendLeft <= initial.textareaRight) failed.push("send button is not to the right of textarea");
  if (initial.sendColor !== "rgb(255, 255, 255)") failed.push("send button text is not white");
  if (afterEnter.turns < 1) failed.push("enter key did not create a turn");
  if (afterEnter.value) failed.push("input was not cleared after enter send");
  if (afterAsk.turns < 1) failed.push("question did not create a turn");
  if (afterAsk.recommendationCards < 1) failed.push("recommendation cards missing");
  if (!afterAsk.hasNoHelpLabel) failed.push("feedback no-help label missing");
  if (afterPersonCardClick.heading !== "智能问答") failed.push("person card navigated away from ask page");
  if (afterPersonCardClick.detailLabel !== "人员详情") failed.push("person detail sidebar did not open");
  if (afterPersonCardClick.profilePageVisible) failed.push("person card opened profile page");
  if (afterRelatedContentClick.heading !== "智能问答") failed.push("related content navigated away from ask page");
  if (afterRelatedContentClick.detailLabel !== "内容详情") failed.push("related content detail sidebar did not open");
  if (afterNewChatTwice.emptySessions !== 1) failed.push("new chat did not reuse existing empty session");
  if (directory.personCards < 6) failed.push("directory cards missing");
  if (!mine.hasProfileDetail || mine.blockCount < 4) failed.push("mine overview blocks missing");
  if (!mine.portraitColumns.includes("px") || mine.portraitColumns.split(" ").length < 2) failed.push("mine portraits are not side by side");
  if (!mine.actionText.includes("为他人画像")) failed.push("mine review entry missing");
  if (exceptions.length) failed.push("runtime exceptions found");

  console.log(JSON.stringify(result, null, 2));
  if (failed.length) {
    console.error(`Smoke test failed: ${failed.join(", ")}`);
    process.exitCode = 1;
  }
} finally {
  if (ws) ws.close();
  chrome.kill("SIGTERM");
}

function send(method, params = {}) {
  const id = nextId++;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    setTimeout(() => {
      if (!pending.has(id)) return;
      pending.delete(id);
      reject(new Error(`CDP command timed out: ${method}`));
    }, 10000);
  });
}

function waitForEvent(method, timeoutMs) {
  const existing = events.find((event) => event.method === method);
  if (existing) return Promise.resolve(existing);
  return new Promise((resolve, reject) => {
    const startLength = events.length;
    const timer = setTimeout(() => reject(new Error(`Timed out waiting for ${method}`)), timeoutMs);
    const interval = setInterval(() => {
      const found = events.slice(startLength).find((event) => event.method === method);
      if (!found) return;
      clearTimeout(timer);
      clearInterval(interval);
      resolve(found);
    }, 50);
  });
}

async function evaluateObject(fn) {
  const result = await send("Runtime.evaluate", {
    expression: `(${fn.toString()})()`,
    returnByValue: true,
    awaitPromise: true
  });
  return result.result.value;
}

function waitForTab(port) {
  return retry(async () => {
    const tabs = await requestJson(`http://127.0.0.1:${port}/json`);
    const tab = tabs.find((item) => item.type === "page");
    if (!tab) throw new Error("No page tab available");
    return tab;
  }, 10000);
}

async function retry(fn, timeoutMs) {
  const startedAt = Date.now();
  let lastError;
  while (Date.now() - startedAt < timeoutMs) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      await delay(100);
    }
  }
  throw lastError;
}

function requestJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (response) => {
      let body = "";
      response.setEncoding("utf8");
      response.on("data", (chunk) => { body += chunk; });
      response.on("end", () => {
        try {
          resolve(JSON.parse(body));
        } catch (error) {
          reject(error);
        }
      });
    }).on("error", reject);
  });
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

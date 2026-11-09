// Bounded real Chromium UI checks using Node's built-in WebSocket; no downloads.
import { spawn, execFileSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { createInterface } from "node:readline";

const directory = process.argv[2];
const candidates = [
  process.env.SHIPSENSE_CHROME,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
].filter(Boolean);
const executable = candidates.find((path) => existsSync(path));
if (!executable || !directory) throw new Error("EXISTING_CHROMIUM_REQUIRED");
const version = execFileSync(
  process.platform === "win32" ? "powershell" : executable,
  process.platform === "win32"
    ? [
        "-NoProfile",
        "-Command",
        "(Get-Item -LiteralPath $env:SHIPSENSE_BROWSER_EXECUTABLE).VersionInfo.ProductVersion",
      ]
    : ["--version"],
  {
    timeout: 10_000,
    windowsHide: true,
    env: { ...process.env, SHIPSENSE_BROWSER_EXECUTABLE: executable },
  },
)
  .toString()
  .trim();
if (!/\d+\.\d+\.\d+/.test(version))
  throw new Error("BROWSER_VERSION_UNAVAILABLE");
writeFileSync(
  join(directory, "browser.json"),
  JSON.stringify({ executable, version }) + "\n",
);
const browser = spawn(
  executable,
  [
    "--headless=new",
    "--remote-debugging-address=127.0.0.1",
    "--remote-debugging-port=0",
    `--user-data-dir=${join(directory, "browser-profile")}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-sync",
    "--disable-extensions",
    "--window-size=1024,768",
    "about:blank",
  ],
  { stdio: "ignore", windowsHide: true },
);
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const deadline = setTimeout(() => {
  browser.kill();
  process.exit(2);
}, 240_000);
let socket;
let sequence = 0;
let responses = 0;
const pending = new Map();
function call(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error("BROWSER_COMMAND_TIMEOUT"));
    }, 10_000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await call("Runtime.evaluate", {
    expression,
    returnByValue: true,
  });
  if (result.exceptionDetails) throw new Error("BROWSER_EVALUATION_FAILED");
  return result.result.value;
}
async function waitFor(expression) {
  for (let count = 0; count < 100; count++) {
    if (await evaluate(expression)) return;
    await pause(100);
  }
  throw new Error("BROWSER_STATE_MISMATCH");
}
try {
  const portFile = join(directory, "browser-profile", "DevToolsActivePort");
  for (let count = 0; !existsSync(portFile) && count < 100; count++)
    await pause(100);
  const port = Number(readFileSync(portFile, "utf8").split("\n")[0]);
  if (!Number.isInteger(port) || port < 1 || port > 65535)
    throw new Error("BROWSER_PORT_INVALID");
  const tabs = await (
    await fetch(`http://127.0.0.1:${port}/json/list`, {
      signal: AbortSignal.timeout(5_000),
      redirect: "error",
    })
  ).json();
  const tab = tabs.find((item) => item.type === "page");
  const debugging = new URL(tab.webSocketDebuggerUrl);
  if (
    debugging.protocol !== "ws:" ||
    debugging.hostname !== "127.0.0.1" ||
    Number(debugging.port) !== port ||
    !debugging.pathname.startsWith("/devtools/page/")
  )
    throw new Error("BROWSER_TARGET_REFUSED");
  socket = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });
  socket.addEventListener("message", ({ data }) => {
    const message = JSON.parse(data);
    if (
      message.method === "Network.responseReceived" &&
      message.params.response.url === "http://127.0.0.1:3000/api/foundation"
    )
      responses++;
    const request = pending.get(message.id);
    if (!request) return;
    clearTimeout(request.timer);
    pending.delete(message.id);
    if (message.error) request.reject(new Error("BROWSER_PROTOCOL_FAILED"));
    else request.resolve(message.result);
  });
  await call("Page.enable");
  await call("Network.enable");
  await call("Page.navigate", { url: "http://127.0.0.1:3000" });
  await waitFor("!!document.querySelector('.retry-button')");
  console.log("BROWSER_READY");
  for await (const command of createInterface({ input: process.stdin })) {
    if (command === "quit") break;
    if (!["connected", "unavailable", "recovered"].includes(command))
      throw new Error("BROWSER_INPUT_INVALID");
    await waitFor(
      "document.querySelector('.retry-button')?.getAttribute('aria-disabled') === 'false'",
    );
    const previousResponses = responses;
    await evaluate(
      "document.querySelector('.retry-button').focus(); document.querySelector('.retry-button').click()",
    );
    for (
      let attempt = 0;
      responses <= previousResponses && attempt < 100;
      attempt++
    )
      await pause(100);
    if (responses <= previousResponses)
      throw new Error("BROWSER_RETRY_NOT_OBSERVED");
    await waitFor(
      "document.querySelector('.retry-button')?.getAttribute('aria-disabled') === 'false'",
    );
    await waitFor(
      command === "unavailable"
        ? "document.querySelector('[role=status]')?.textContent.includes('unavailable') && !document.querySelector('dl') && !!document.querySelector('.request-reference span')"
        : "document.querySelector('[role=status]')?.textContent === 'Connected' && document.querySelector('dd')?.textContent === '0.1.0-dev'",
    );
    if (
      !(await evaluate(
        "document.activeElement === document.querySelector('.retry-button')",
      ))
    )
      throw new Error("BROWSER_FOCUS_LOST");
    const capture = await call("Page.captureScreenshot", { format: "png" });
    writeFileSync(
      join(directory, `${command}.png`),
      Buffer.from(capture.data, "base64"),
    );
    console.log(`BROWSER_${command.toUpperCase()}`);
  }
} catch {
  console.log("BROWSER_SMOKE_FAILED");
  process.exitCode = 2;
} finally {
  clearTimeout(deadline);
  if (socket?.readyState === WebSocket.OPEN) {
    try {
      await call("Browser.close");
    } catch {
      /* Process fallback below. */
    }
  }
  for (const request of pending.values()) clearTimeout(request.timer);
  socket?.close();
  if (browser.exitCode === null) {
    await Promise.race([
      new Promise((resolve) => browser.once("exit", resolve)),
      pause(5_000),
    ]);
    if (browser.exitCode === null) browser.kill();
  }
}

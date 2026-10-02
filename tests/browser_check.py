#!/usr/bin/env python3
"""Dependency-free WebDriver checks. Runs in a separate automation browser session."""
import argparse
import base64
import json
from pathlib import Path
import socket
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Browser:
    def __init__(self, name, extension=None):
        port = free_port()
        self.url = f"http://127.0.0.1:{port}"
        self.session = None
        self.name = name
        self.log = open(ROOT / "test-results" / f"{name}-driver.log", "w")
        chrome_driver = ROOT / "build/tools/chromedriver-mac-arm64/chromedriver"
        command = ["safaridriver", "-p", str(port)] if name == "safari" else [str(chrome_driver) if chrome_driver.exists() else "chromedriver", f"--port={port}"]
        self.process = subprocess.Popen(command, stdout=self.log, stderr=self.log)
        for _ in range(50):
            try:
                self.request("GET", "/status")
                break
            except (OSError, RuntimeError):
                time.sleep(0.1)
        capabilities = {"browserName": name, "pageLoadStrategy": "eager"}
        if name == "chrome":
            capabilities["goog:loggingPrefs"] = {"browser": "ALL"}
            chrome_args = ["--autoplay-policy=no-user-gesture-required"]
            if extension:
                chrome_args += [f"--disable-extensions-except={extension}", f"--load-extension={extension}"]
            capabilities["goog:chromeOptions"] = {"args": chrome_args}
            test_chrome = ROOT / "build/tools/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
            if extension and test_chrome.exists():
                capabilities["goog:chromeOptions"]["binary"] = str(test_chrome)
        try:
            session = self.request("POST", "/session", {"capabilities": {"alwaysMatch": capabilities}})
            self.session = session["sessionId"]
            self.capabilities = session["capabilities"]
            self.request("POST", "/timeouts", {"script": 30000, "pageLoad": 45000})
        except Exception:
            self.close()
            raise

    def request(self, method, path, data=None):
        prefix = f"/session/{self.session}" if self.session else ""
        request = urllib.request.Request(self.url + prefix + path, method=method,
                                         data=json.dumps(data).encode() if data is not None else None,
                                         headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=50) as response:
                result = json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(error.read().decode()) from error
        return result.get("value")

    def script(self, script, *args):
        return self.request("POST", "/execute/sync", {"script": script, "args": list(args)})

    def screenshot(self, name):
        (ROOT / "test-results" / f"{self.name}-{name}.png").write_bytes(
            base64.b64decode(self.request("GET", "/screenshot")))

    def close(self):
        if self.session:
            try:
                self.request("DELETE", "")
            except (OSError, RuntimeError):
                pass
        self.process.terminate()
        self.process.wait(timeout=10)
        self.log.close()


def live_probe(browser):
    browser.request("POST", "/url", {"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"})
    for _ in range(40):
        info = browser.script("""
            const v = document.querySelector('#movie_player video');
            if (v) { v.muted = true; v.play().catch(() => {}); }
            return {title: document.title, video: !!v, ready: v?.readyState,
                    width: v?.videoWidth, height: v?.videoHeight,
                    error: document.querySelector('.ytp-error-content-wrap')?.textContent};
        """)
        if info.get("ready", 0) >= 2:
            break
        time.sleep(0.5)
    result = browser.script("""
        const v = document.querySelector('#movie_player video');
        const p = document.querySelector('#movie_player');
        if (!v || v.readyState < 2) return {ok: false, reason: 'No playable video frame'};
        const c = document.createElement('canvas'); c.width = 160; c.height = 90;
        let draw = false, readable = false, error = null;
        try {
            const ctx = c.getContext('2d'); ctx.drawImage(v, 0, 0, 160, 90); draw = true;
            try { ctx.getImageData(0, 0, 1, 1); readable = true; } catch (_) {}
        } catch (e) { error = e.message; }
        const old = p.getAttribute('style');
        const width = Math.min(innerWidth * .7, innerHeight * .7 * v.videoWidth / v.videoHeight);
        p.style.setProperty('width', width + 'px', 'important');
        p.style.setProperty('height', width * v.videoHeight / v.videoWidth + 'px', 'important');
        const rect = p.getBoundingClientRect();
        if (old === null) p.removeAttribute('style'); else p.setAttribute('style', old);
        return {ok: draw && Math.abs(rect.width - width) < 2, draw, readable, error,
                frameCallback: typeof v.requestVideoFrameCallback === 'function',
                actual: {width: rect.width, height: rect.height}, expectedWidth: width};
    """)
    browser.screenshot("live-probe")
    return {"page": info, "probe": result}


def ambient_probe(browser):
    result = None
    for _ in range(80):
        result = browser.script(r"""
            const c = document.querySelector('#yt-ambient-backdrop');
            const primary = document.querySelector('ytd-watch-flexy #primary');
            const secondary = document.querySelector('ytd-watch-flexy #secondary');
            const masthead = document.querySelector('ytd-masthead');
            const below = document.querySelector('ytd-watch-flexy #below');
            if (!c || Number(c.dataset.frames) < 1) {
                return {ok: false, reason: 'Waiting for ambient frame'};
            }
            const pixels = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
            let colorful = 0, samples = 0;
            for (let i = 3; i < pixels.length; i += 64) {
                const red = pixels[i - 3], green = pixels[i - 2], blue = pixels[i - 1];
                if (Math.max(red, green, blue) - Math.min(red, green, blue) > 20) colorful++;
                samples++;
            }
            const rect = primary?.getBoundingClientRect();
            const playerRect = document.querySelector('#movie_player')?.getBoundingClientRect();
            const playerContainerRect = document.querySelector('#player')?.getBoundingClientRect();
            const fullBleedRect = document.querySelector('#player-full-bleed-container')?.getBoundingClientRect();
            const active = document.documentElement.classList.contains('yt-ambient-focus');
            const sidebarHidden = !!secondary && getComputedStyle(secondary).display === 'none';
            const chromeHidden = !!masthead && !!below &&
                getComputedStyle(masthead).display === 'none' && getComputedStyle(below).display === 'none';
            const centered = !!rect &&
                Math.abs(rect.left + rect.width / 2 - innerWidth / 2) < innerWidth * .08 &&
                Math.abs(rect.top + rect.height / 2 - innerHeight / 2) < innerHeight * .08;
            const filtered = getComputedStyle(c).filter.includes('blur');
            const layer = getComputedStyle(document.querySelector('ytd-app')).backgroundColor;
            const alpha = Number(layer.match(/rgba?\([^)]*,\s*([\d.]+)\)$/)?.[1] ?? 1);
            const translucent = alpha <= .2;
            const frames = Number(c.dataset.frames);
            return {ok: active && sidebarHidden && chromeHidden && centered && translucent &&
                        filtered && frames > 1 && colorful > 5,
                    active, sidebarHidden, chromeHidden, centered, translucent, layer, filtered,
                    frames, colorful, samples,
                    primary: rect && {left: rect.left, top: rect.top, width: rect.width, height: rect.height},
                    player: playerRect && {left: playerRect.left, top: playerRect.top,
                        width: playerRect.width, height: playerRect.height},
                    playerContainer: playerContainerRect && {left: playerContainerRect.left,
                        top: playerContainerRect.top, width: playerContainerRect.width,
                        height: playerContainerRect.height},
                    fullBleed: fullBleedRect && {left: fullBleedRect.left, top: fullBleedRect.top,
                        width: fullBleedRect.width, height: fullBleedRect.height},
                    viewport: {width: innerWidth, height: innerHeight},
                    canvas: {width: c.width, height: c.height}};
        """)
        if result and result.get("ok"):
            break
        time.sleep(0.25)
    if result is None:
        result = {"ok": False, "reason": "Page changed while reading extension state"}
    if result.get("ok"):
        initial_frames = result["frames"]
        time.sleep(6)
        stability = browser.script("""
            const canvas = document.querySelector('#yt-ambient-backdrop');
            const video = document.querySelector('#movie_player video.html5-main-video');
            const delayedLayers = ['#cinematics', '#cinematics-container', '#player-full-bleed-container']
                .map(selector => {
                    const element = document.querySelector(selector);
                    if (!element) return {selector, present: false};
                    const style = getComputedStyle(element);
                    return {selector, present: true, display: style.display, opacity: style.opacity,
                            background: style.backgroundColor, zIndex: style.zIndex};
                });
            return {frames: Number(canvas?.dataset.frames || 0),
                    canvasVideoTime: Number(canvas?.dataset.videoTime || 0),
                    videoTime: video?.currentTime, readyState: video?.readyState, delayedLayers};
        """)
        stability["advanced"] = stability["frames"] >= initial_frames + 20
        stability["fresh"] = abs(stability["videoTime"] - stability["canvasVideoTime"]) < 1
        result["stability"] = stability
        result["ok"] = result["ok"] and stability["advanced"] and stability["fresh"]

    if result.get("ok"):
        style = browser.script("""
            const button = document.querySelector('.yt-ambient-style-toggle');
            button.click();
            const canvas = document.querySelector('#yt-ambient-backdrop');
            return {gradient: document.documentElement.classList.contains('yt-ambient-gradient'),
                    focusActive: document.documentElement.classList.contains('yt-ambient-focus'),
                    label: button.textContent, width: canvas?.width, height: canvas?.height,
                    filtered: getComputedStyle(canvas).filter.includes('blur')};
        """)
        result["style"] = style
        result["ok"] = result["ok"] and style["gradient"] and style["focusActive"] \
            and style["label"] == "GRAD" and style["width"] == 12 and style["height"] >= 4 \
            and style["filtered"]

    if result.get("ok"):
        toggle = browser.script("""
            const button = document.querySelector('.yt-ambient-toggle');
            const canvas = document.querySelector('#yt-ambient-backdrop');
            const masthead = document.querySelector('ytd-masthead');
            const below = document.querySelector('ytd-watch-flexy #below');
            const start = performance.now();
            button.focus();
            button.click();
            return {milliseconds: performance.now() - start,
                    focusActive: document.documentElement.classList.contains('yt-ambient-focus'),
                    gradientActive: document.documentElement.classList.contains('yt-ambient-gradient'),
                    canvasRemoved: canvas.isConnected === false,
                    mastheadRestored: getComputedStyle(masthead).display !== 'none',
                    belowRestored: getComputedStyle(below).display !== 'none',
                    buttonBlurred: document.activeElement !== button,
                    pressed: button.getAttribute('aria-pressed')};
        """)
        result["toggle"] = toggle
        result["ok"] = result["ok"] and not toggle["focusActive"] and not toggle["gradientActive"] \
            and toggle["canvasRemoved"] and toggle["mastheadRestored"] and toggle["belowRestored"] \
            and toggle["buttonBlurred"] and toggle["pressed"] == "false" \
            and toggle["milliseconds"] < 50
        time.sleep(0.2)
        result["toggle"]["layout"] = browser.script("""
            const rect = selector => {
                const value = document.querySelector(selector)?.getBoundingClientRect();
                return value && {left: value.left, top: value.top,
                    width: value.width, height: value.height};
            };
            return {player: rect('#movie_player'), playerContainer: rect('#player'),
                    primary: rect('ytd-watch-flexy #primary'),
                    columns: rect('ytd-watch-flexy #columns')};
        """)
        layout = result["toggle"]["layout"]
        result["ok"] = result["ok"] and layout["player"]["width"] <= layout["primary"]["width"] \
            and abs(layout["player"]["width"] - layout["playerContainer"]["width"]) < 2 \
            and abs(layout["player"]["height"] - layout["playerContainer"]["height"]) < 2
        browser.script("document.querySelector('.ytp-size-button')?.click(); document.querySelector('.yt-ambient-toggle').click()")
        time.sleep(0.5)
        result["reactivation"] = browser.script("""
            const rect = selector => {
                const value = document.querySelector(selector)?.getBoundingClientRect();
                return value && {left: value.left, top: value.top,
                    width: value.width, height: value.height};
            };
            return {player: rect('#movie_player'), playerContainer: rect('#player'),
                    fullBleed: rect('#player-full-bleed-container'),
                    primary: rect('ytd-watch-flexy #primary'),
                    watchAttributes: [...document.querySelector('ytd-watch-flexy').attributes]
                        .map(attribute => attribute.name)};
        """)
        reactivation = result["reactivation"]
        expected_width = min(1280, result["viewport"]["width"] * .86,
                             result["viewport"]["height"] * .86 * 16 / 9)
        result["ok"] = result["ok"] \
            and abs(reactivation["player"]["left"] + reactivation["player"]["width"] / 2
                    - result["viewport"]["width"] / 2) < 2 \
            and abs(reactivation["player"]["width"] - expected_width) < 2
        result["escape"] = browser.script("""
            const canvas = document.querySelector('#yt-ambient-backdrop');
            document.dispatchEvent(new KeyboardEvent('keydown',
                {key: 'Escape', bubbles: true}));
            return {focusActive: document.documentElement.classList.contains('yt-ambient-focus'),
                    gradientActive: document.documentElement.classList.contains('yt-ambient-gradient'),
                    canvasRemoved: canvas.isConnected === false,
                    pressed: document.querySelector('.yt-ambient-toggle')?.getAttribute('aria-pressed')};
        """)
        escape = result["escape"]
        result["ok"] = result["ok"] and not escape["focusActive"] \
            and not escape["gradientActive"] and escape["canvasRemoved"] \
            and escape["pressed"] == "false"
    browser.screenshot("ambient")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("browser", choices=["safari", "chrome"])
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--extension", type=Path)
    args = parser.parse_args()
    (ROOT / "test-results").mkdir(exist_ok=True)
    extension = args.extension.resolve() if args.extension else None
    browser = Browser(args.browser, extension)
    try:
        result = {"capabilities": browser.capabilities}
        if args.live:
            result["live"] = live_probe(browser)
        if extension:
            result["ambient"] = ambient_probe(browser)
            if not result["ambient"].get("ok"):
                logs = browser.request("POST", "/log", {"type": "browser"})
                result["ambient"]["browserLog"] = [
                    entry for entry in logs if "chrome-extension://" in entry["message"]
                ]
        print(json.dumps(result, indent=2))
        (ROOT / "test-results" / f"{args.browser}.json").write_text(json.dumps(result, indent=2) + "\n")
        if (args.live and not result["live"]["probe"].get("ok")) or (extension and not result["ambient"].get("ok")):
            raise SystemExit(1)
    finally:
        browser.close()


if __name__ == "__main__":
    main()

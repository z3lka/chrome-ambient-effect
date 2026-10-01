# YouTube Ambient Focus

A small Chrome extension that centers the YouTube player, hides sidebar
recommendations, and reflects the video's colors into a blurred, darkened
background.

## Install in Chrome

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Choose **Load unpacked** and select the `chrome` directory in this project.
4. Open a YouTube video. Ambient focus starts automatically.

Use the **GLOW** player control or the extension's toolbar button to toggle the
effect.

## Browser check

```sh
python3 tests/browser_check.py chrome --live --extension chrome
```

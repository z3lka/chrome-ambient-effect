# Ambient Focus for YouTube™

A small, open-source Chrome extension that turns a YouTube watch page into a
focused viewing space. It centers the player, hides surrounding distractions,
and reflects the current video's colors into an ambient background.

![Ambient Focus enabled on a YouTube watch page](store-assets/screenshot-1.png)

## Features

- Centers the video player and hides the header, recommendations, chat, and
  content below the player.
- Offers blurred-video and sampled-gradient ambient backgrounds.
- Toggles instantly from the **GLOW** player control or the extension toolbar
  button.
- Restores the normal page layout when disabled.
- Uses no analytics, accounts, tracking, remote code, or external services.

## Install from source

1. Download or clone this repository.
2. Open `chrome://extensions` in Chrome.
3. Enable **Developer mode**.
4. Choose **Load unpacked** and select the repository's `chrome` directory.
5. Open a YouTube video.

The extension activates automatically on watch pages. Use **GLOW** to turn the
focused layout on or off, press **Escape** to return to the normal layout, and
use **BLUR**/**GRAD** to change the background style.

## Privacy

Ambient Focus reads the current video frames only inside the open YouTube watch
page to draw the background locally. Frames are not stored, transmitted, or
shared. See the full [privacy policy](PRIVACY.md).

## Development

The extension uses plain JavaScript and CSS with no build step or runtime
dependencies. The uploadable extension is the contents of `chrome` with
`manifest.json` at the root.

To create a release archive:

```sh
mkdir -p dist
cd chrome
zip -r ../dist/ambient-focus-for-youtube-0.1.0.zip . -x '*.DS_Store'
```

To run the live browser check, install a ChromeDriver version compatible with
your Chrome version and run:

```sh
python3 tests/browser_check.py chrome --live --extension chrome
```

The check opens a separate automated browser session and writes ignored output
to `test-results`.

## Contributing

Bug reports and focused pull requests are welcome. Please describe the YouTube
page state that triggered the issue and run the browser check when changing
layout or rendering behavior.

## Release resources

Copy-ready Chrome Web Store text and submission notes are in
[STORE_LISTING.md](STORE_LISTING.md). Store artwork lives in `store-assets` and
is intentionally excluded from the extension ZIP.

## License

[MIT](LICENSE)

YouTube is a trademark of Google LLC. This project is independent and is not
affiliated with, endorsed by, or sponsored by Google LLC.

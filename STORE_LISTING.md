# Chrome Web Store submission

This file contains copy-ready listing and privacy text for version `0.1.0`.

## Product details

**Name**

> Ambient Focus for YouTube™

**Summary**

> Centers the video, hides distractions, and creates a local ambient background on YouTube™.

**Category:** Productivity  
**Language:** English

**Detailed description**

> Ambient Focus turns YouTube watch pages into a calm, centered viewing space.
>
> - Center the video player and hide the header, recommendations, chat, and content below the player.
> - Choose a blurred-video background or a smooth gradient sampled from the current video.
> - Toggle the complete effect from the GLOW player control or the extension toolbar button.
> - Return to YouTube's normal layout instantly when the effect is disabled.
>
> Video frames are processed only inside the current browser tab to draw the background. The extension does not retain or transmit user data. It has no analytics, ads, accounts, tracking, external services, or remotely hosted code.
>
> YouTube is a trademark of Google LLC. This extension is independent and is not affiliated with, endorsed by, or sponsored by Google LLC.

## Graphic assets

- Store icon: `chrome/icons/icon128.png` (128×128 PNG)
- Screenshot: `store-assets/screenshot-1.png` (1280×800 PNG)
- Small promo tile: `store-assets/promo-small.png` (440×280 PNG)
- Marquee promo tile: optional and not included
- Promotional video: optional and not included

## Privacy practices

**Single purpose**

> Create a distraction-free YouTube watch page by centering the video player, hiding surrounding page elements, and rendering a locally generated ambient background from the current video.

**Site access justification — `https://www.youtube.com/*`**

> Required to add the GLOW and BLUR/GRAD player controls, modify the watch-page layout, and read current video frames for the locally rendered ambient background. The extension does not run on any other website.

**Remote code:** Select **No, I am not using remote code**.

**Data disclosure:** Select **Website content** because current video frames are
processed locally. Do not select other data types unless the implementation
changes. In the limited-use certification, confirm that website content is used
only for the extension's described user-facing feature and is not sold,
transferred, or used for advertising or creditworthiness.

**Privacy policy URL**

> https://github.com/z3lka/chrome-ambient-effect/blob/main/PRIVACY.md

The repository must be public before submission so this URL is accessible to
reviewers without signing in.

## URLs

- Homepage: `https://github.com/z3lka/chrome-ambient-effect`
- Support: `https://github.com/z3lka/chrome-ambient-effect/issues`

## Reviewer note

> Open any standard YouTube watch page. Ambient Focus activates automatically. GLOW toggles the focused layout; BLUR/GRAD changes the ambient rendering style. All processing is local to the tab, and the source is available at the homepage URL.

## Submission checklist

- [ ] Make the GitHub repository public and confirm the privacy/support URLs work while signed out.
- [ ] Run the live browser check against the final `chrome` directory.
- [ ] Build the ZIP and confirm `manifest.json` is at its root.
- [ ] Upload the ZIP and the three graphic assets listed above.
- [ ] Paste the product details and privacy-practice answers from this file.
- [ ] Confirm developer contact email, distribution regions, and public visibility.
- [ ] Review the preview, then submit for review.

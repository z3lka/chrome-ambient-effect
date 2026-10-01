(() => {
  const ROOT_CLASS = "yt-ambient-focus";
  const BUTTON_CLASS = "yt-ambient-toggle";
  const CANVAS_ID = "yt-ambient-backdrop";

  let active = false;
  let glowEnabled = true;
  let video;
  let canvas;
  let drawTimer;
  let setupTimer;
  let frameCount = 0;

  const currentVideo = () => document.querySelector("#movie_player video.html5-main-video");

  function updateButtons() {
    for (const button of document.querySelectorAll(`.${BUTTON_CLASS}`)) {
      button.setAttribute("aria-pressed", String(glowEnabled));
      button.title = glowEnabled ? "Disable background glow" : "Enable background glow";
      button.setAttribute("aria-label", button.title);
    }
  }

  function installButton() {
    const controls = document.querySelector("#movie_player .ytp-right-controls");
    if (!controls || controls.querySelector(`.${BUTTON_CLASS}`)) return;

    const button = document.createElement("button");
    button.type = "button";
    button.className = `ytp-button ${BUTTON_CLASS}`;
    button.textContent = "GLOW";
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggle();
    });
    controls.prepend(button);
    updateButtons();
  }

  function drawCover(context, source) {
    const sourceRatio = source.videoWidth / source.videoHeight;
    const targetRatio = canvas.width / canvas.height;
    let sx = 0;
    let sy = 0;
    let sw = source.videoWidth;
    let sh = source.videoHeight;

    if (sourceRatio > targetRatio) {
      sw = sh * targetRatio;
      sx = (source.videoWidth - sw) / 2;
    } else {
      sh = sw / targetRatio;
      sy = (source.videoHeight - sh) / 2;
    }
    context.drawImage(source, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
  }

  function drawFrame() {
    if (!active || !glowEnabled || !video || !canvas) return;

    const nextVideo = currentVideo();
    if (nextVideo && nextVideo !== video) {
      attachVideo();
      return;
    }

    try {
      if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
        const height = Math.max(72, Math.round(128 * innerHeight / innerWidth));
        if (canvas.width !== 128 || canvas.height !== height) {
          canvas.width = 128;
          canvas.height = height;
        }
        drawCover(canvas.getContext("2d"), video);
        canvas.dataset.frames = String(++frameCount);
        canvas.dataset.videoTime = String(video.currentTime);
      }
    } catch (error) {
      canvas.dataset.error = error.name;
    } finally {
      if (active && glowEnabled) drawTimer = setTimeout(drawFrame, 80);
    }
  }

  function detachVideo() {
    clearTimeout(drawTimer);
    drawTimer = undefined;
    video = undefined;
    canvas?.remove();
    canvas = undefined;
  }

  function attachVideo() {
    const nextVideo = currentVideo();
    if (!nextVideo || (nextVideo === video && canvas?.isConnected)) return;

    detachVideo();
    video = nextVideo;
    canvas = document.createElement("canvas");
    canvas.id = CANVAS_ID;
    canvas.dataset.frames = "0";
    canvas.setAttribute("aria-hidden", "true");
    document.body.prepend(canvas);
    if (glowEnabled) drawFrame();
  }

  function start() {
    active = true;
    document.documentElement.classList.add(ROOT_CLASS);
    document.documentElement.classList.toggle("yt-ambient-glow-off", !glowEnabled);
    setupPlayer();
    updateButtons();
  }

  function stop() {
    active = false;
    clearTimeout(setupTimer);
    document.documentElement.classList.remove(ROOT_CLASS, "yt-ambient-glow-off");
    detachVideo();
    updateButtons();
  }

  function toggle() {
    glowEnabled = !glowEnabled;
    document.documentElement.classList.toggle("yt-ambient-glow-off", !glowEnabled);
    clearTimeout(drawTimer);
    if (glowEnabled) drawFrame();
    updateButtons();
  }

  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === "yt-ambient-focus:toggle") toggle();
  });

  function setupPlayer(attempt = 0) {
    clearTimeout(setupTimer);
    installButton();
    attachVideo();
    if ((!video || !document.querySelector(`.${BUTTON_CLASS}`)) && attempt < 40) {
      setupTimer = setTimeout(() => setupPlayer(attempt + 1), 250);
    }
  }

  document.addEventListener("yt-navigate-finish", () => {
    if (location.pathname === "/watch") start();
    else stop();
  });
  addEventListener("resize", () => {
    if (!active || !glowEnabled) return;
    clearTimeout(drawTimer);
    drawFrame();
  });

  if (location.pathname === "/watch") start();
})();

(() => {
  const ROOT_CLASS = "yt-ambient-focus";
  const BUTTON_CLASS = "yt-ambient-toggle";
  const STYLE_BUTTON_CLASS = "yt-ambient-style-toggle";
  const GRADIENT_CLASS = "yt-ambient-gradient";
  const CANVAS_ID = "yt-ambient-backdrop";

  let active = false;
  let enabled = true;
  let backdropStyle = "blur";
  let video;
  let canvas;
  let drawTimer;
  let setupTimer;
  let frameCount = 0;

  const currentVideo = () => document.querySelector("#movie_player video.html5-main-video");

  function updateButtons() {
    for (const button of document.querySelectorAll(`.${BUTTON_CLASS}`)) {
      button.setAttribute("aria-pressed", String(enabled));
      button.title = enabled ? "Disable ambient focus" : "Enable ambient focus";
      button.setAttribute("aria-label", button.title);
    }
    for (const button of document.querySelectorAll(`.${STYLE_BUTTON_CLASS}`)) {
      const gradient = backdropStyle === "gradient";
      button.textContent = gradient ? "GRAD" : "BLUR";
      button.title = gradient ? "Use blurred video background" : "Use color gradient background";
      button.setAttribute("aria-pressed", String(gradient));
      button.setAttribute("aria-label", button.title);
    }
  }

  function installButton() {
    const controls = document.querySelector("#movie_player .ytp-right-controls");
    if (!controls) return;

    if (!controls.querySelector(`.${BUTTON_CLASS}`)) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `ytp-button ${BUTTON_CLASS}`;
      button.textContent = "GLOW";
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.blur();
        toggle();
      });
      controls.prepend(button);
    }

    if (!controls.querySelector(`.${STYLE_BUTTON_CLASS}`)) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `ytp-button ${STYLE_BUTTON_CLASS}`;
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.blur();
        backdropStyle = backdropStyle === "blur" ? "gradient" : "blur";
        document.documentElement.classList.toggle(GRADIENT_CLASS, active && backdropStyle === "gradient");
        clearTimeout(drawTimer);
        if (active) drawFrame();
        updateButtons();
      });
      controls.prepend(button);
    }
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
    if (!active || !video || !canvas) return;

    const nextVideo = currentVideo();
    if (nextVideo && nextVideo !== video) {
      attachVideo();
      return;
    }

    try {
      if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
        const width = backdropStyle === "gradient" ? 12 : 128;
        const height = Math.max(backdropStyle === "gradient" ? 4 : 72,
          Math.round(width * innerHeight / innerWidth));
        if (canvas.width !== width || canvas.height !== height) {
          canvas.width = width;
          canvas.height = height;
        }
        drawCover(canvas.getContext("2d"), video);
        canvas.dataset.frames = String(++frameCount);
        canvas.dataset.videoTime = String(video.currentTime);
      }
    } catch (error) {
      canvas.dataset.error = error.name;
    } finally {
      if (active) drawTimer = setTimeout(drawFrame, 80);
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
    drawFrame();
  }

  function start() {
    active = enabled;
    document.documentElement.classList.toggle(ROOT_CLASS, active);
    document.documentElement.classList.toggle(GRADIENT_CLASS, active && backdropStyle === "gradient");
    setupPlayer();
    updateButtons();
    requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
  }

  function stop() {
    const wasActive = active;
    active = false;
    clearTimeout(setupTimer);
    document.documentElement.classList.remove(ROOT_CLASS, GRADIENT_CLASS);
    detachVideo();
    updateButtons();
    if (wasActive) requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
  }

  function toggle() {
    enabled = !enabled;
    if (enabled && location.pathname === "/watch") start();
    else {
      stop();
      if (location.pathname === "/watch") setupPlayer();
    }
  }

  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === "yt-ambient-focus:toggle") toggle();
  });

  function setupPlayer(attempt = 0) {
    clearTimeout(setupTimer);
    installButton();
    if (active) attachVideo();
    if (((active && !video) || !document.querySelector(`.${BUTTON_CLASS}`) ||
        !document.querySelector(`.${STYLE_BUTTON_CLASS}`)) && attempt < 40) {
      setupTimer = setTimeout(() => setupPlayer(attempt + 1), 250);
    }
  }

  document.addEventListener("yt-navigate-finish", () => {
    if (location.pathname === "/watch") start();
    else stop();
  });
  addEventListener("resize", () => {
    if (!active) return;
    clearTimeout(drawTimer);
    drawFrame();
  });
  addEventListener("keydown", (event) => {
    if (event.key === "Escape" && active) toggle();
  }, true);

  if (location.pathname === "/watch") start();
})();

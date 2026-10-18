// Gentle falling snow drawn on one fixed canvas. Clicks pass straight through it.
// Turned off for visitors who prefer reduced motion or have data saver on.
// Enable or disable for the whole site with SNOW_EFFECT in app.py.
(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const saveData = navigator.connection && navigator.connection.saveData;
  if (reduceMotion || saveData) return;

  const canvas = document.createElement("canvas");
  canvas.className = "snowfall";
  canvas.setAttribute("aria-hidden", "true");
  document.body.append(canvas);
  const ctx = canvas.getContext("2d");

  const COLOR = "176, 200, 222";   // pale ice blue, visible on white
  let width = 0;
  let height = 0;
  let flakes = [];

  function flakeCount() {
    // About 45 on a desktop screen, fewer on small screens.
    return Math.round(Math.min(45, Math.max(16, (width * height) / 26000)));
  }

  function makeFlake(startAnywhere) {
    const size = 1.2 + Math.random() * 2.6;
    return {
      x: Math.random() * width,
      y: startAnywhere ? Math.random() * height : -10 - Math.random() * height * 0.3,
      r: size,
      speed: 0.25 + size * 0.12 + Math.random() * 0.2,      // bigger flakes fall a little faster
      drift: 0.15 + Math.random() * 0.35,                    // sideways sway amount
      phase: Math.random() * Math.PI * 2,
      alpha: 0.35 + Math.random() * 0.4,
      star: size > 3.2,                                       // the largest are drawn as snowflakes
      spin: Math.random() * Math.PI,
    };
  }

  function resize() {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    const target = flakeCount();
    while (flakes.length < target) flakes.push(makeFlake(true));
    flakes.length = target;
  }

  function drawStar(f) {
    // Six arms, like the logo.
    const arm = f.r * 2.1;
    ctx.save();
    ctx.translate(f.x, f.y);
    ctx.rotate(f.spin);
    ctx.strokeStyle = `rgba(${COLOR}, ${f.alpha})`;
    ctx.lineWidth = 1.1;
    ctx.lineCap = "round";
    ctx.beginPath();
    for (let i = 0; i < 6; i += 1) {
      const a = (Math.PI / 3) * i;
      ctx.moveTo(0, 0);
      ctx.lineTo(Math.cos(a) * arm, Math.sin(a) * arm);
    }
    ctx.stroke();
    ctx.restore();
  }

  let last = performance.now();
  function frame(now) {
    const dt = Math.min((now - last) / 16.7, 3);   // frame-rate independent; caps big jumps
    last = now;
    ctx.clearRect(0, 0, width, height);
    for (const f of flakes) {
      f.phase += 0.012 * dt;
      f.y += f.speed * dt;
      f.x += Math.sin(f.phase) * f.drift * dt;
      f.spin += 0.004 * dt;
      if (f.y > height + 10) Object.assign(f, makeFlake(false));
      if (f.x < -10) f.x = width + 10;
      if (f.x > width + 10) f.x = -10;
      if (f.star) {
        drawStar(f);
      } else {
        ctx.beginPath();
        ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${COLOR}, ${f.alpha})`;
        ctx.fill();
      }
    }
    requestAnimationFrame(frame);   // browsers pause this automatically in hidden tabs
  }

  resize();
  window.addEventListener("resize", resize, { passive: true });
  requestAnimationFrame(frame);
})();

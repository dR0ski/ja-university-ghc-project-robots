# Static media placeholders

Drop production assets in this directory:

- `hero.mp4` — vertical 9:16 H.264 baseline, ≤ 5 MB, ≤ 12 s loop, audio stripped.
- `hero.webm` — VP9 alt source, same dimensions.
- `hero-poster.jpg` — first-frame poster, ~80 KB, 1080×1920 recommended.

Until these exist, the splash hero will render with the gradient overlay only;
no console errors thanks to graceful `<video>` fallback.

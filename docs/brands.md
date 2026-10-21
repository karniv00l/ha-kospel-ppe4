# Adding a brand icon (removes "logo not available")

Home Assistant pulls integration icons/logos from the central
[home-assistant/brands](https://github.com/home-assistant/brands) repository.
Until `kospel_ppe4` is added there, HA shows a placeholder. This is purely
cosmetic and does not affect functionality.

## Ready-made assets

This repo already ships a fitting icon in [`docs/logo/`](logo/):

- [`icon.svg`](logo/icon.svg) — editable vector source (orange flame + water drop)
- [`icon.png`](logo/icon.png) — 256x256, transparent
- [`icon@2x.png`](logo/icon@2x.png) — 512x512, transparent

To re-render after editing the SVG (macOS):

```bash
qlmanage -t -s 512 -o docs/logo docs/logo/icon.svg
magick docs/logo/icon.svg.png -alpha set -fuzz 10% \
  -fill none -floodfill +0+0 white -fill none -floodfill +511+0 white \
  -fill none -floodfill +0+511 white -fill none -floodfill +511+511 white \
  docs/logo/icon@2x.png
magick docs/logo/icon@2x.png -resize 256x256 docs/logo/icon.png
rm docs/logo/icon.svg.png
```

## What to submit

In a fork of `home-assistant/brands`, copy the PNGs to:

```
custom_integrations/kospel_ppe4/icon.png        # <- docs/logo/icon.png   (256x256)
custom_integrations/kospel_ppe4/icon@2x.png     # <- docs/logo/icon@2x.png (512x512)
```

Requirements (see the brands repo README):

- **Square**, **transparent** background, trimmed of padding (the shipped files
  already satisfy this).
- `icon@2x.png` is exactly 2x `icon.png`.
- PNG, optimized (the repo CI runs an image check).

This is an **original** mark, not Kospel's trademarked logo, so there are no brand
rights concerns in submitting it.

## Submit

1. Fork `home-assistant/brands`, add the files above.
2. Open a PR. CI validates dimensions/format.
3. Once merged, HA shows the icon automatically (no integration change needed).

> Tip: if you have the Kospel logo as a high-res PNG/SVG, it can be exported to
> the exact sizes above with any image editor, or `magick logo.svg -resize 256x256
> -background none icon.png`.

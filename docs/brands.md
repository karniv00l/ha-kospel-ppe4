# Brand icon

Home Assistant shows an integration icon on the device/integration pages. Since
**Home Assistant 2026.3.0**, a custom integration can ship its own brand images
directly — they no longer have to be submitted to the central
[home-assistant/brands](https://github.com/home-assistant/brands) repository
(which now auto-closes new custom-integration PRs).

## How it works here

This integration bundles its icon in
[`custom_components/kospel_ppe4/brand/`](../custom_components/kospel_ppe4/brand):

```
custom_components/kospel_ppe4/brand/
├── icon.png        # 256x256, transparent
└── icon@2x.png     # 512x512, transparent (hDPI)
```

Local brand images take priority over the brands CDN, so the icon appears as
soon as the integration is installed — no extra configuration, no external PR,
no waiting for a merge. Supported filenames are `icon.png`, `icon@2x.png`,
`logo.png`, `logo@2x.png`, and their `dark_` variants.

See the announcement:
<https://contributors.home-assistant.io/blog/2026/02/24/brands-proxy-api/>

## Editing the icon

The editable source lives in [`docs/logo/`](logo/):

- [`icon.svg`](logo/icon.svg) — vector source (orange flame + water drop)
- [`icon.png`](logo/icon.png) — 256x256, transparent
- [`icon@2x.png`](logo/icon@2x.png) — 512x512, transparent

To re-render after editing the SVG (macOS) and refresh the bundled copies:

```bash
qlmanage -t -s 512 -o docs/logo docs/logo/icon.svg
magick docs/logo/icon.svg.png -alpha set -fuzz 10% \
  -fill none -floodfill +0+0 white -fill none -floodfill +511+0 white \
  -fill none -floodfill +0+511 white -fill none -floodfill +511+511 white \
  docs/logo/icon@2x.png
magick docs/logo/icon@2x.png -resize 256x256 docs/logo/icon.png
rm docs/logo/icon.svg.png
cp docs/logo/icon.png docs/logo/icon@2x.png custom_components/kospel_ppe4/brand/
```

The mark is **original** (not Kospel's trademarked logo), so there are no brand
rights concerns.

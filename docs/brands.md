# Adding a brand icon (removes "logo not available")

Home Assistant pulls integration icons/logos from the central
[home-assistant/brands](https://github.com/home-assistant/brands) repository.
Until `kospel_ppe4` is added there, HA shows a placeholder. This is purely
cosmetic and does not affect functionality.

## What to submit

In a fork of `home-assistant/brands`, create:

```
custom_integrations/kospel_ppe4/icon.png        # 256x256, square, transparent PNG
custom_integrations/kospel_ppe4/icon@2x.png     # 512x512
custom_integrations/kospel_ppe4/logo.png        # optional, wordmark (max 512 high)
custom_integrations/kospel_ppe4/logo@2x.png     # optional
```

Requirements (see the brands repo README):

- **Square** `icon.png` with a **transparent** background, trimmed of padding.
- `icon.png` = 256x256, `icon@2x.png` = 512x512 (exactly 2x).
- PNG, optimized (the repo CI runs an image check).
- Use the Kospel brand mark (the orange flame logo). Make sure you have the right
  to use it — brands are accepted as representing the manufacturer.

## Submit

1. Fork `home-assistant/brands`, add the files above.
2. Open a PR. CI validates dimensions/format.
3. Once merged, HA shows the icon automatically (no integration change needed).

> Tip: if you have the Kospel logo as a high-res PNG/SVG, it can be exported to
> the exact sizes above with any image editor, or `magick logo.svg -resize 256x256
> -background none icon.png`.

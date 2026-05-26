# HSgram Premium Assets

Internal premium media assets used to restore and compare HSgram premium surfaces.

This repository is intentionally separated from `HSgram_server`. The main server repository should only contain code that reads assets from a configured directory. Large Telegram reference media should live here and be deployed beside the server.

## Contents

- `official_promo/`
  - `premium_promo_meta.json`: metadata returned by Telegram `help.getPremiumPromo`.
  - `videos/official_*.mp4`: official promo videos, keyed by section name.
- `official_premium_stickers/`
  - `official_premium_stickers_and_status_meta.json`: metadata for premium large stickers and emoji status sets.
  - `files/*.tgs`: official premium sticker/status animation documents pulled for internal comparison.
- `public_premium_demos/`
  - `videos/*.mp4`: converted public Telegram Premium demo animations from TelegramOfficial/Premium.
- `tools/`
  - `pull_telegram_official_assets.py`: helper script for pulling Telegram featured sticker packs, featured custom emoji packs, premium sticker search results, emoji statuses, and other default sticker sets from an authorized Telegram session.

## Notes

- Keep this repository private.
- Do not store Telegram login sessions, phone numbers, verification codes, or 2FA secrets here.
- The server code should consume these files as deploy-time assets instead of committing large binaries into the main server repository.

## Server Usage

`HSgram_server` should read this repository as a runtime asset directory, for example:

```bash
git clone git@github.com:kkk511github/HSgram_-premium-promo.git /opt/hsgram-premium-assets
export HSGRAM_PREMIUM_ASSETS_DIR=/opt/hsgram-premium-assets
```

When deploying with Docker or compose, mount the directory read-only:

```yaml
services:
  teamgram:
    volumes:
      - /opt/hsgram-premium-assets:/opt/hsgram-premium-assets:ro
    environment:
      HSGRAM_PREMIUM_ASSETS_DIR: /opt/hsgram-premium-assets
```

The server should fall back gracefully if this env var is missing, but premium demo videos, official premium stickers, and emoji status assets will only be available when the directory is mounted.

## Refreshing Official Assets

Use an already-authorized Telethon session outside the repository. Never commit the session file.

```bash
/tmp/hsgram-telethon/bin/python tools/pull_telegram_official_assets.py \
  --session /tmp/hsgram_official_premium_promo/official_premium_live.session \
  --output telegram_official_catalog
```

The script pulls public Telegram surfaces only:

- `messages.getFeaturedStickers`
- `messages.getFeaturedEmojiStickers`
- `messages.getStickers("⭐️⭐️")`
- `messages.getStickers("📂⭐️")`
- Telegram default emoji/status/premium special sticker sets

It does not pull private user uploads, `messages.getMyStickers`, or the account's installed sticker list.

After refreshing:

```bash
git status
git add .
git commit -m "Refresh Telegram official assets"
git push
```

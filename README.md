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
- `telegram_official_catalog/`
  - `reactions/metadata.json`: metadata returned by Telegram `messages.getAvailableReactions`.
  - `reactions/files/*`: official reaction static icons and reaction animations.
  - `featured_stickers/`, `featured_emoji_stickers/`, `premium_stickers/`, `special_sets/`: official/default Telegram sticker and emoji catalogs used by the server as the default catalog.
- `tools/`
  - `pull_telegram_official_assets.py`: helper script for pulling Telegram available reactions, featured sticker packs, featured custom emoji packs, premium sticker search results, emoji statuses, and other default sticker sets from an authorized Telegram session.

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

The server should fall back gracefully if this env var is missing. When the directory is mounted, official Telegram assets are used as the default source for premium demo videos, premium stickers, emoji statuses, featured/default sticker catalogs, and reaction assets. Existing Admin import paths remain available as fallback/extension data.

## Refreshing Official Assets

Use an already-authorized Telethon session outside the repository. Never commit the session file.

```bash
/tmp/hsgram-telethon/bin/python tools/pull_telegram_official_assets.py \
  --session /tmp/hsgram_official_premium_promo/official_premium_live.session \
  --output telegram_official_catalog
```

The script pulls public Telegram surfaces only:

- `messages.getAvailableReactions`
- `messages.getFeaturedStickers`
- `messages.getFeaturedEmojiStickers`
- `messages.getStickers("⭐️⭐️")`
- `messages.getStickers("📂⭐️")`
- Telegram default emoji/status/premium special sticker sets

To refresh only reaction assets:

```bash
/tmp/hsgram-telethon/bin/python tools/pull_telegram_official_assets.py \
  --session /tmp/hsgram_official_premium_promo/official_premium_live.session \
  --output telegram_official_catalog \
  --only-reactions
```

It does not pull private user uploads, `messages.getMyStickers`, or the account's installed sticker list.

After refreshing:

```bash
git status
git add .
git commit -m "Refresh Telegram official assets"
git push
```

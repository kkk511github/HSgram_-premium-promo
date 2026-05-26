# HSgram Premium Assets

Internal premium media assets used to restore and compare HSgram premium surfaces.

## Contents

- `official_promo/`
  - `premium_promo_meta.json`: metadata returned by Telegram `help.getPremiumPromo`.
  - `videos/official_*.mp4`: official promo videos, keyed by section name.
- `official_premium_stickers/`
  - `official_premium_stickers_and_status_meta.json`: metadata for premium large stickers and emoji status sets.
  - `files/*.tgs`: official premium sticker/status animation documents pulled for internal comparison.
- `public_premium_demos/`
  - `videos/*.mp4`: converted public Telegram Premium demo animations from TelegramOfficial/Premium.

## Notes

- Keep this repository private.
- Do not store Telegram login sessions, phone numbers, verification codes, or 2FA secrets here.
- The server code should consume these files as deploy-time assets instead of committing large binaries into the main server repository.

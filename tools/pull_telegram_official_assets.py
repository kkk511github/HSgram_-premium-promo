#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import re
from pathlib import Path

from telethon import TelegramClient, functions, types
from telethon.network import ConnectionTcpAbridged


def safe_name(value):
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return value.strip("._") or "set"


def document_ext(document):
    mime_type = getattr(document, "mime_type", "") or ""
    if mime_type == "application/x-tgsticker":
        return "tgs"
    if mime_type == "video/webm":
        return "webm"
    if mime_type == "image/webp":
        return "webp"
    if mime_type == "video/mp4":
        return "mp4"
    return "bin"


def document_meta(document, local_file=None):
    result = {
        "id": document.id,
        "access_hash": document.access_hash,
        "file_reference_hex": bytes(document.file_reference or b"").hex(),
        "mime_type": document.mime_type,
        "size": document.size,
        "dc_id": document.dc_id,
        "attributes": [attribute.to_dict() for attribute in document.attributes],
    }
    if local_file is not None:
        result["local_file"] = str(local_file)
    return result


def sticker_set_meta(sticker_set):
    return sticker_set.to_dict()


async def download_document(client, document, output_dir, index):
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{index:04d}_{document.id}.{document_ext(document)}"
    path = output_dir / file_name
    if path.exists() and path.stat().st_size == document.size:
        return path
    tmp_path = path.with_suffix(path.suffix + ".part")
    if tmp_path.exists():
        tmp_path.unlink()
    await client.download_media(document, file=str(tmp_path))
    tmp_path.replace(path)
    return path


async def fetch_full_set(client, input_set, output_root, key, sleep_seconds):
    result = await client(functions.messages.GetStickerSetRequest(stickerset=input_set, hash=0))
    sticker_set = result.set
    set_dir_name = f"{safe_name(sticker_set.short_name)}_{sticker_set.id}"
    set_dir = output_root / "sets" / set_dir_name
    file_dir = set_dir / "files"
    documents = []
    for index, document in enumerate(result.documents or []):
        local_file = await download_document(client, document, file_dir, index)
        documents.append(document_meta(document, local_file.relative_to(output_root)))
        if sleep_seconds > 0:
            await asyncio.sleep(sleep_seconds)
    metadata = {
        "source": key,
        "set": sticker_set_meta(sticker_set),
        "packs": [pack.to_dict() for pack in (result.packs or [])],
        "documents": documents,
    }
    metadata_path = set_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


async def fetch_featured(client, request, output_root, key, sleep_seconds):
    output_root.mkdir(parents=True, exist_ok=True)
    featured = await client(request)
    catalog = {
        "source": key,
        "hash": getattr(featured, "hash", None),
        "count": getattr(featured, "count", None),
        "premium": getattr(featured, "premium", None),
        "sets": [],
    }
    covered_sets = list(getattr(featured, "sets", []) or [])
    for index, covered in enumerate(covered_sets):
        sticker_set = getattr(covered, "set", None)
        if sticker_set is None:
            continue
        print(f"[{key}] {index + 1}/{len(covered_sets)} {sticker_set.short_name} ({sticker_set.count})", flush=True)
        input_set = types.InputStickerSetID(id=sticker_set.id, access_hash=sticker_set.access_hash)
        try:
            metadata = await fetch_full_set(client, input_set, output_root, key, sleep_seconds)
            catalog["sets"].append({
                "set": metadata["set"],
                "metadata_file": str((output_root / "sets" / f"{safe_name(sticker_set.short_name)}_{sticker_set.id}" / "metadata.json").relative_to(output_root)),
            })
        except Exception as exc:
            catalog["sets"].append({
                "set": sticker_set_meta(sticker_set),
                "error": repr(exc),
            })
        (output_root / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return catalog


async def fetch_search_documents(client, emoticon, output_root, key, sleep_seconds):
    output_root.mkdir(parents=True, exist_ok=True)
    result = await client(functions.messages.GetStickersRequest(emoticon=emoticon, hash=0))
    documents = []
    file_dir = output_root / "files"
    stickers = list(getattr(result, "stickers", []) or [])
    for index, document in enumerate(stickers):
        local_file = await download_document(client, document, file_dir, index)
        documents.append(document_meta(document, local_file.relative_to(output_root)))
        if sleep_seconds > 0:
            await asyncio.sleep(sleep_seconds)
    metadata = {
        "source": f"messages.getStickers({emoticon!r})",
        "hash": getattr(result, "hash", None),
        "count": len(stickers),
        "documents": documents,
    }
    (output_root / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


async def fetch_special_sets(client, output_root, sleep_seconds):
    specs = [
        ("emoji_default_statuses", types.InputStickerSetEmojiDefaultStatuses()),
        ("emoji_channel_default_statuses", types.InputStickerSetEmojiChannelDefaultStatuses()),
        ("emoji_default_topic_icons", types.InputStickerSetEmojiDefaultTopicIcons()),
        ("emoji_generic_animations", types.InputStickerSetEmojiGenericAnimations()),
        ("animated_emoji", types.InputStickerSetAnimatedEmoji()),
        ("animated_emoji_animations", types.InputStickerSetAnimatedEmojiAnimations()),
        ("premium_gifts", types.InputStickerSetPremiumGifts()),
    ]
    catalog = []
    for key, input_set in specs:
        print(f"[special] {key}", flush=True)
        try:
            metadata = await fetch_full_set(client, input_set, output_root, key, sleep_seconds)
            catalog.append({
                "key": key,
                "set": metadata["set"],
                "metadata_file": str((output_root / "sets" / f"{safe_name(metadata['set']['short_name'])}_{metadata['set']['id']}" / "metadata.json").relative_to(output_root)),
            })
        except Exception as exc:
            catalog.append({"key": key, "error": repr(exc)})
        output_root.mkdir(parents=True, exist_ok=True)
        (output_root / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return catalog


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", default="/tmp/hsgram_official_premium_promo/official_premium_live.session")
    parser.add_argument("--api-id", type=int, default=int(os.environ.get("TELEGRAM_API_ID", "24547280")))
    parser.add_argument("--api-hash", default=os.environ.get("TELEGRAM_API_HASH", "3ae3c1b4aa1af9954e28ac446ec6dbf2"))
    parser.add_argument("--output", default="telegram_official_catalog")
    parser.add_argument("--sleep", type=float, default=0.02)
    parser.add_argument("--skip-featured-stickers", action="store_true")
    parser.add_argument("--skip-featured-emoji", action="store_true")
    args = parser.parse_args()

    output = Path(args.output)
    client = TelegramClient(args.session, args.api_id, args.api_hash, connection=ConnectionTcpAbridged)
    await client.connect()
    if not await client.is_user_authorized():
        raise SystemExit("Telegram session is not authorized")

    if not args.skip_featured_stickers:
        await fetch_featured(
            client,
            functions.messages.GetFeaturedStickersRequest(hash=0),
            output / "featured_stickers",
            "messages.getFeaturedStickers",
            args.sleep,
        )
    if not args.skip_featured_emoji:
        await fetch_featured(
            client,
            functions.messages.GetFeaturedEmojiStickersRequest(hash=0),
            output / "featured_emoji_stickers",
            "messages.getFeaturedEmojiStickers",
            args.sleep,
        )
    await fetch_search_documents(client, "⭐️⭐️", output / "premium_stickers" / "large", "premium_large_stickers", args.sleep)
    await fetch_search_documents(client, "📂⭐️", output / "premium_stickers" / "all", "premium_all_stickers", args.sleep)
    await fetch_special_sets(client, output / "special_sets", args.sleep)
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

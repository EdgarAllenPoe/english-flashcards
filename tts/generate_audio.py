#!/usr/bin/env python3
"""Generate one web-ready MP3 file per English flashcard entry."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from piper import PiperVoice, SynthesisConfig

EXPECTED_HEADERS = ("English", "Spanish")
EXPECTED_CARD_COUNT = 684
VOICE_NAME = "en_US-ryan-high"

# Exact forms used for entries that text-to-speech systems commonly misread.
PRONUNCIATION_OVERRIDES: dict[str, str] = {
    "application / app": "application, or app",
    "Wi-Fi": "Wi-Fi",
    "teaching assistant / TA": "teaching assistant, or T A",
    "CPU": "C P U",
    "SQL": "S Q L",
    "README": "read me",
    "Big O notation": "Big O notation",
    "AVL tree": "A V L tree",
    "address (memory)": "address, in memory",
    "process ID": "process I D",
    "IP address": "I P address",
    "DNS": "D N S",
    "HTTP": "H T T P",
    "HTTPS": "H T T P S",
    "TCP": "T C P",
    "UDP": "U D P",
    "NP": "N P",
    "NP-hard": "N P hard",
    "NP-complete": "N P complete",
    "AutoSum": "auto sum",
    "SUM": "sum",
    "AVERAGE": "average",
    "MIN": "min",
    "MAX": "max",
    "COUNT": "count",
    "IF": "if",
    "IFERROR": "if error",
    "SUMIF": "sum if",
    "SUMIFS": "sum ifs",
    "COUNTIF": "count if",
    "COUNTIFS": "count ifs",
    "XLOOKUP": "X lookup",
    "MATCH": "match",
    "INDEX/MATCH": "index match",
    "Find and Replace": "find and replace",
    "PivotTable": "pivot table",
    "PivotChart": "pivot chart",
    "CSV file": "C S V file",
}


@dataclass(frozen=True)
class Card:
    card_id: str
    english: str
    spanish: str
    spoken_text: str
    audio_file: str


def run(command: list[str]) -> str:
    """Run a command and return stdout, raising a useful error on failure."""
    completed = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed ({completed.returncode}): {' '.join(command)}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed.stdout.strip()


def validate_tools() -> None:
    missing = [tool for tool in ("ffmpeg", "ffprobe") if shutil.which(tool) is None]
    if missing:
        raise RuntimeError(f"Required command(s) not found: {', '.join(missing)}")


def spoken_form(english: str) -> str:
    """Return a natural spoken form, with deliberate acronym pronunciation."""
    text = PRONUNCIATION_OVERRIDES.get(english, english).strip()
    # A final period gives isolated words and phrases a natural ending cadence.
    return text if text.endswith((".", "!", "?")) else f"{text}."


def load_cards(csv_path: Path) -> list[Card]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        headers = tuple(reader.fieldnames or ())
        if headers != EXPECTED_HEADERS:
            raise ValueError(
                f"Expected CSV headers {EXPECTED_HEADERS}, but found {headers}."
            )

        rows: list[tuple[str, str]] = []
        for row_number, row in enumerate(reader, start=2):
            english = (row.get("English") or "").strip()
            spanish = (row.get("Spanish") or "").strip()
            if not english or not spanish:
                raise ValueError(f"Blank English or Spanish value on CSV row {row_number}.")
            rows.append((english, spanish))

    if len(rows) != EXPECTED_CARD_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_CARD_COUNT} cards, but the CSV contains {len(rows)}."
        )

    english_values = [english.casefold() for english, _ in rows]
    if len(set(english_values)) != len(english_values):
        duplicates = sorted(
            {value for value in english_values if english_values.count(value) > 1}
        )
        raise ValueError(f"Duplicate English entries found: {duplicates}")

    cards: list[Card] = []
    for index, (english, spanish) in enumerate(rows, start=1):
        card_id = f"{index:04d}"
        cards.append(
            Card(
                card_id=card_id,
                english=english,
                spanish=spanish,
                spoken_text=spoken_form(english),
                audio_file=f"audio/{card_id}.mp3",
            )
        )
    return cards


def encode_mp3(wav_path: Path, mp3_path: Path) -> None:
    # Mono 80 kbps MP3 is compact and more than sufficient for spoken vocabulary.
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(wav_path),
            "-map_metadata",
            "-1",
            "-ac",
            "1",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "80k",
            str(mp3_path),
        ]
    )


def probe_audio(mp3_path: Path) -> tuple[float, int, int, int]:
    output = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=sample_rate,channels,bit_rate:format=duration",
            "-of",
            "json",
            str(mp3_path),
        ]
    )
    data = json.loads(output)
    stream = data["streams"][0]
    duration = float(data["format"]["duration"])
    sample_rate = int(stream["sample_rate"])
    channels = int(stream["channels"])
    bit_rate = int(stream.get("bit_rate") or 0)
    return duration, sample_rate, channels, bit_rate


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest_csv(output_dir: Path, rows: Iterable[dict[str, object]]) -> None:
    rows = list(rows)
    fieldnames = [
        "CardID",
        "English",
        "Spanish",
        "SpokenText",
        "AudioFile",
        "DurationSeconds",
        "SampleRateHz",
        "Channels",
        "BitRateKbps",
        "FileSizeBytes",
        "SHA256",
    ]
    with (output_dir / "audio-manifest.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json_files(
    output_dir: Path,
    cards: list[Card],
    manifest_rows: list[dict[str, object]],
    total_duration: float,
) -> None:
    website_manifest = [
        {
            "id": card.card_id,
            "english": card.english,
            "spanish": card.spanish,
            "audio": card.audio_file,
            "spokenText": card.spoken_text.rstrip("."),
        }
        for card in cards
    ]
    (output_dir / "audio-manifest.json").write_text(
        json.dumps(website_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "audio-map.json").write_text(
        json.dumps(
            {card.english: card.audio_file for card in cards},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    summary = {
        "voice": VOICE_NAME,
        "engine": "Piper neural text-to-speech",
        "cardCount": len(cards),
        "audioFileCount": len(manifest_rows),
        "format": "MP3",
        "channels": 1,
        "nominalBitRateKbps": 80,
        "totalDurationSeconds": round(total_duration, 3),
        "pronunciationOverrideCount": len(PRONUNCIATION_OVERRIDES),
    }
    (output_dir / "generation-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_preview(output_dir: Path, cards: list[Card]) -> None:
    items = []
    for card in cards[:30]:
        items.append(
            "<article><div>"
            + html.escape(card.spanish)
            + "</div><audio controls preload=\"none\" src=\""
            + html.escape(card.audio_file, quote=True)
            + "\"></audio></article>"
        )
    preview = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Muestra de audio</title><style>
body{font-family:system-ui,sans-serif;max-width:680px;margin:auto;padding:24px;background:#f5f7fb;color:#172033}
h1{font-size:1.6rem}p{line-height:1.5}article{background:white;border:1px solid #dbe2ef;border-radius:14px;padding:16px;margin:12px 0;font-size:1.1rem;font-weight:650}audio{width:100%;margin-top:10px}
</style></head><body><h1>Muestra de pronunciación</h1>
<p>Las palabras en inglés permanecen ocultas. Esta página permite escuchar las primeras 30 tarjetas.</p>
""" + "\n".join(items) + "\n</body></html>\n"
    (output_dir / "preview.html").write_text(preview, encoding="utf-8")


def write_readme(output_dir: Path, cards: list[Card]) -> None:
    readme = f"""# English Flashcard Audio Files

This package contains **{len(cards)} individual English pronunciation files** generated for the supplied `English,Spanish` vocabulary list.

## Voice and format

- Neural voice: `{VOICE_NAME}` (American English male)
- Audio: MP3, mono, nominal 80 kbps
- Filenames: `audio/0001.mp3` through `audio/{len(cards):04d}.mp3`
- The English word is not exposed in the audio filename.

These clips are synthesized speech, not recordings of a person speaking each entry live.

## Files

- `audio/` — one MP3 per flashcard
- `audio-manifest.csv` — full human-readable filename map and technical validation data
- `audio-manifest.json` — website-friendly list
- `audio-map.json` — simple English-to-audio-path lookup object
- `generation-summary.json` — generation totals
- `preview.html` — browser preview of the first 30 cards, showing Spanish only
- `vocabulary.csv` — the validated source vocabulary

## Website mapping

The `AudioFile` value in the CSV manifest and the `audio` value in the JSON manifest are relative paths. For example, card `0001` uses `audio/0001.mp3`.

Technical acronyms and spreadsheet formulas use deliberate spoken forms. For example, `CPU` is spoken letter by letter, `README` is spoken as “read me,” and `INDEX/MATCH` is spoken as “index match.”
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    validate_tools()
    if not args.csv.is_file():
        raise FileNotFoundError(args.csv)
    if not args.model.is_file():
        raise FileNotFoundError(args.model)
    config_path = Path(str(args.model) + ".json")
    if not config_path.is_file():
        raise FileNotFoundError(config_path)

    cards = load_cards(args.csv)
    output_dir = args.output.resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(parents=True)
    shutil.copy2(args.csv, output_dir / "vocabulary.csv")

    print(f"Loading neural voice model: {args.model}", flush=True)
    voice = PiperVoice.load(str(args.model), config_path=str(config_path))
    synthesis_config = SynthesisConfig(
        length_scale=1.08,
        noise_scale=0.667,
        noise_w_scale=0.8,
        normalize_audio=True,
        volume=1.0,
    )

    manifest_rows: list[dict[str, object]] = []
    total_duration = 0.0

    with tempfile.TemporaryDirectory(prefix="flashcard-audio-") as temp_directory:
        temp_dir = Path(temp_directory)
        for index, card in enumerate(cards, start=1):
            wav_path = temp_dir / f"{card.card_id}.wav"
            mp3_path = output_dir / card.audio_file
            with wave.open(str(wav_path), "wb") as wav_file:
                voice.synthesize_wav(
                    card.spoken_text,
                    wav_file,
                    syn_config=synthesis_config,
                )
            encode_mp3(wav_path, mp3_path)

            duration, sample_rate, channels, bit_rate = probe_audio(mp3_path)
            file_size = mp3_path.stat().st_size
            if not (0.20 <= duration <= 12.0):
                raise ValueError(
                    f"Unexpected duration for {card.card_id} ({card.english!r}): {duration}"
                )
            if channels != 1:
                raise ValueError(f"Expected mono audio for {mp3_path}, got {channels} channels")
            if file_size < 1000:
                raise ValueError(f"Audio file is unexpectedly small: {mp3_path}")

            total_duration += duration
            manifest_rows.append(
                {
                    "CardID": card.card_id,
                    "English": card.english,
                    "Spanish": card.spanish,
                    "SpokenText": card.spoken_text.rstrip("."),
                    "AudioFile": card.audio_file,
                    "DurationSeconds": f"{duration:.3f}",
                    "SampleRateHz": sample_rate,
                    "Channels": channels,
                    "BitRateKbps": round(bit_rate / 1000) if bit_rate else 0,
                    "FileSizeBytes": file_size,
                    "SHA256": sha256_file(mp3_path),
                }
            )

            if index == 1 or index % 25 == 0 or index == len(cards):
                print(f"Generated and validated {index}/{len(cards)} files", flush=True)

    mp3_files = sorted(audio_dir.glob("*.mp3"))
    if len(mp3_files) != len(cards):
        raise RuntimeError(
            f"Expected {len(cards)} MP3 files, but found {len(mp3_files)}."
        )

    write_manifest_csv(output_dir, manifest_rows)
    write_json_files(output_dir, cards, manifest_rows, total_duration)
    write_preview(output_dir, cards)
    write_readme(output_dir, cards)

    print(
        f"Complete: {len(mp3_files)} files; total duration {total_duration:.1f} seconds",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - surface full context in Actions logs
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        raise

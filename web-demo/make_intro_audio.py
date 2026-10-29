#!/usr/bin/env python3
"""Make the spoken intro for the home page: intro_en.mp3 and intro_de.mp3.

    ELEVENLABS_API_KEY=... python3 make_intro_audio.py      (or put the key in ../.env)

The clips are generated once and committed, like the quiz audio in Teach-It-To-Grandma, so the static
GitHub Pages site can play them without an API key in the browser. Re-run after changing a script below.
ELEVENLABS_VOICE_ID overrides the voice (default: George, a warm narrator).
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
ENDPOINT = "https://api.elevenlabs.io/v1/text-to-speech/"
DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
# Multilingual, so one voice reads both versions.
MODEL_ID = "eleven_multilingual_v2"

SCRIPTS = {
    "en": (
        "Hi, I'm Caire. I help Caritas in Würzburg find companies in Mainfranken that share its values. "
        "I've researched hundreds of local businesses, their social engagement and their past donations, "
        "and scored how well each one fits the work Caritas does: childcare, elderly care, counselling and more. "
        "Green means approach now, yellow means worth a look. "
        "Every score comes with its reasons and sources. Ready? Explore the map."
    ),
    "de": (
        "Hallo, ich bin Caire. Ich helfe der Caritas in Würzburg, Unternehmen in Mainfranken zu finden, die ihre Werte teilen. "
        "Ich habe Hunderte regionale Firmen recherchiert, ihr soziales Engagement und ihre bisherigen Spenden, "
        "und bewertet, wie gut jede zur Arbeit der Caritas passt: Kinderbetreuung, Altenpflege, Beratung und mehr. "
        "Grün heißt: jetzt ansprechen, Gelb: einen Blick wert. "
        "Jede Bewertung hat ihre Gründe und Quellen. Bereit? Entdecken Sie die Karte."
    ),
}


def load_dotenv(path: Path = HERE.parent / ".env") -> None:
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and key and not key.startswith("#"):
                os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def speak(text: str, key: str, voice: str) -> bytes:
    req = urllib.request.Request(
        ENDPOINT + voice + "?output_format=mp3_44100_128",
        data=json.dumps({"text": text, "model_id": MODEL_ID,
                         "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}).encode("utf-8"),
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main() -> None:
    load_dotenv()
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set (put it in ../.env, never in the web pages)")
    voice = os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)
    for lang in sys.argv[1:] or SCRIPTS:
        out = HERE / f"intro_{lang}.mp3"
        out.write_bytes(speak(SCRIPTS[lang], key, voice))
        print(f"wrote {out.name} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

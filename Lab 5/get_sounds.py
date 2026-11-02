"""Download real animal recordings from Wikimedia Commons and make them the monster's trip sounds.

    python get_sounds.py

Run it on the Pi (it needs internet and ffmpeg: sudo apt install -y ffmpeg).
It writes:
  sounds/trip2.wav    2nd trip: a real growl
  sounds/trip3.wav    3rd trip and after: a real cat hiss, then the growl
  sounds/CREDITS.txt  author + license of each recording (put this in your readme: the
                      Creative Commons licenses require crediting the author)
The 1st trip keeps the monster's spoken "Huh?". To use a different recording, pass its
Commons file name, e.g.  python get_sounds.py --growl "File:Giant Feline Sounds.ogg"
"""
import argparse
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

import requests

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "Lab5MonsterBot/1.0 (https://github.com/Gtpatel02/Interactive-Lab-Hub; student project) python-requests"}
HERE = Path(__file__).resolve().parent
OUT = HERE / "sounds"
RAW = OUT / "raw"

GROWLS = ["File:Bear growl.ogg", "File:Giant Feline Sounds.ogg", "File:Monster growls.ogg"]
HISS_CATEGORY = "Category:Audio files of cats hissing"


def api(**params):
    params.update(format="json", formatversion=2)
    r = requests.get(API, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def info(title: str):
    """URL, author and license of one Commons file, or None if it doesn't exist."""
    pages = api(action="query", titles=title, prop="imageinfo", iiprop="url|mime|extmetadata")["query"]["pages"]
    page = pages[0]
    if page.get("missing") or "imageinfo" not in page:
        return None
    ii = page["imageinfo"][0]
    meta = ii.get("extmetadata", {})
    strip = lambda s: html.unescape(re.sub("<[^>]+>", "", s or "")).strip()
    return {
        "title": page["title"], "url": ii["url"], "mime": ii.get("mime", ""),
        "page": ii.get("descriptionurl", ""),
        "author": strip(meta.get("Artist", {}).get("value")) or "unknown",
        "license": strip(meta.get("LicenseShortName", {}).get("value")) or "see page",
    }


def first_audio_in(category: str):
    members = api(action="query", list="categorymembers", cmtitle=category, cmtype="file",
                  cmlimit=50)["query"]["categorymembers"]
    for m in members:
        i = info(m["title"])
        if i and i["mime"].startswith(("audio/", "application/ogg", "video/webm")):
            return i
    return None


def download(i) -> Path:
    name = re.sub(r"[^A-Za-z0-9._-]", "_", i["title"].split(":", 1)[1])
    path = RAW / name
    if not path.exists():
        r = requests.get(i["url"].split("?")[0], headers=HEADERS, timeout=120)
        r.raise_for_status()
        path.write_bytes(r.content)
    print(f"  downloaded {i['title']} ({path.stat().st_size // 1024} KB)")
    return path


def clip(src: Path, seconds: float) -> str:
    """ffmpeg filter: skip the silence at the start, keep `seconds`, fade out, even out the loudness."""
    return (f"silenceremove=start_periods=1:start_threshold=-35dB,"
            f"atrim=0:{seconds},afade=t=out:st={max(0.1, seconds - 0.4)}:d=0.4,"
            f"dynaudnorm=f=150:g=15,aresample=22050")


def ffmpeg(args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--growl", help='Commons file for the growl, e.g. "File:Bear growl.ogg"')
    p.add_argument("--hiss", help="Commons file for the hiss (default: first file in the cats-hissing category)")
    p.add_argument("--growl-seconds", type=float, default=2.5)
    p.add_argument("--hiss-seconds", type=float, default=1.5)
    args = p.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is missing: run  sudo apt install -y ffmpeg  and try again")
    RAW.mkdir(parents=True, exist_ok=True)

    print("finding a growl...")
    growl = None
    for title in ([args.growl] if args.growl else GROWLS):
        growl = info(title)
        if growl:
            break
    print("finding a hiss...")
    hiss = info(args.hiss) if args.hiss else first_audio_in(HISS_CATEGORY)
    if not growl:
        sys.exit("couldn't find a growl recording on Commons; pass one with --growl")
    if not hiss:
        print("[warn] no cat hiss found; trip 3 will be the growl only")

    g = download(growl)
    ffmpeg(["-i", str(g), "-ac", "1", "-af", clip(g, args.growl_seconds), str(OUT / "trip2.wav")])
    print("  wrote sounds/trip2.wav (growl)")

    if hiss:
        h = download(hiss)
        ffmpeg(["-i", str(h), "-i", str(g), "-filter_complex",
                f"[0:a]aformat=channel_layouts=mono,{clip(h, args.hiss_seconds)}[a];"
                f"anullsrc=r=22050:cl=mono,atrim=0:0.15[gap];"
                f"[1:a]aformat=channel_layouts=mono,{clip(g, args.growl_seconds)}[b];"
                f"[a][gap][b]concat=n=3:v=0:a=1[out]",
                "-map", "[out]", str(OUT / "trip3.wav")])
        print("  wrote sounds/trip3.wav (hiss + growl)")
    else:
        shutil.copy(OUT / "trip2.wav", OUT / "trip3.wav")

    with open(OUT / "CREDITS.txt", "w") as f:
        f.write("Monster trip sounds, recordings from Wikimedia Commons:\n\n")
        for role, i in [("growl (trips 2 and 3)", growl), ("hiss (trip 3)", hiss)]:
            if i:
                f.write(f"- {role}: \"{i['title']}\" by {i['author']}, {i['license']}, {i['page']}\n")
    print("\n" + (OUT / "CREDITS.txt").read_text())
    print("try them:  aplay sounds/trip2.wav  and  aplay sounds/trip3.wav")


if __name__ == "__main__":
    main()

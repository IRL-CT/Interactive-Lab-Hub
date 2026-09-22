# Lab 3 revision — notes for instructors and TAs

Not for students. Delete or move out of the lab directory before the term starts.

## What the restructure is actually for

The old lab had speech-in and speech-out and nothing in between. Students could
transcribe a file and synthesize a sentence, but the moment they tried to build
something conversational they hit turn-taking with no tools and no vocabulary
for it, usually by writing a fixed-duration `arecord` and discovering that
people do not speak in five-second units.

Section C (VAD and endpointing) is the substantive addition. Everything else is
maintenance. If you only adopt one change, adopt that one.

## Dependency changes

**Removed:**

| Package | Why |
|---|---|
| `vosk` | Last PyPI wheel is 0.3.45, December 2022. Effectively unmaintained. |
| `openai-whisper`, `torch` | ~1 GB of install on arm64 for a timing comparison that `faster-whisper` can make against itself. |
| `spacy`, `thinc`, `blis`, `curated-transformers`, `misaki` | Transitive from the above and from a partially-wired Kokoro setup. |
| `kittentts` | Installed from a raw GitHub release URL, 0.1.x, never referenced in the README. That URL is a single point of failure in the middle of the semester. |
| `pyaudio`, `SpeechRecognition`, `pyttsx3`, `eventlet`, `flask-socketio` | All from the `ollama/` directory, now removed. `pyaudio` needs `portaudio19-dev` to build and was the reason for the second venv. |

**Added:** `sherpa-onnx` (Silero VAD via ONNX Runtime — the `silero-vad` PyPI
package pulls in torch, which defeats the purpose).

**Bumped:** `piper-tts` 1.3 → 1.8. This is a breaking CLI change; see below.

All remaining packages have aarch64 wheels. Nothing compiles from source.
Nothing depends on PyTorch. Install time on a Pi 5 should drop substantially,
though I have not been able to measure it — please time it on real hardware
before class.

## Breaking changes you will hit

1. **Piper.** The `echo 'text' | piper --model X --output_file Y` form in the
   old README does not work in 1.x. It is now
   `python3 -m piper -m VOICE --data-dir DIR -f OUT.wav -- 'text'`, and voices
   must be downloaded explicitly with `python3 -m piper.download_voices`.
   `setup.sh` pre-downloads `en_US-lessac-medium` so nobody is pulling a voice
   over conference wifi.

2. **`pico2wave` / `libttspico-utils`** is gone from current Debian. Dropped
   from `setup.sh`; the demo script it backed is removed.

3. **`GoogleTTS_demo.sh`** hit the undocumented `translate_tts` endpoint through
   mplayer. Removed — it breaks unpredictably and is ToS-dubious to assign.
   Piper covers the "good-sounding voice" slot better anyway.

4. **`requirements.txt`** is now direct dependencies with compatible-release
   pins rather than a 110-line `pip freeze`. If you want the reproducibility the
   freeze was giving you, generate and commit a lockfile:
   `uv pip compile requirements.txt -o requirements.lock`.

## The Ollama section

Removed per your call. If you want to reinstate it later, note that
`phi3:mini` is April-2024 vintage; `gemma3:1b` (~18–22 tok/s on a Pi 5) or
`qwen3:1.7b` are the current equivalents, and the official `ollama` Python
package handles streaming, which matters a lot for perceived latency in a
speech UI. It would slot in cleanly as a replacement for `respond()` in
`echo_bot.py` without needing a second venv.

## Things I could not verify

- Nothing here has been run on actual hardware. The API calls are checked
  against current upstream docs and examples, but `listen.py` and `echo_bot.py`
  need a real Pi with a real microphone before students see them.
- `sherpa_onnx.VadModelConfig` exposes `min_speech_duration`; confirm on the
  installed version, as the field set has shifted across releases.
- Piper's streaming `synthesize()` chunk API (`audio_int16_bytes`,
  `sample_rate`) is from the 1.x Python docs. Worth a smoke test.
- Bluetooth speaker latency may swamp the timing numbers `echo_bot.py` reports.
  If so, either have students use a wired output for Section C or add a note.

## Suggested other files to touch

- `prep.md` — still references Fall2025-shadow image paths; unchanged here.
- `speech-scripts/whisper_try.py`, `faster_whisper_try.py` — superseded by
  `transcribe.py`, should be deleted.
- `speech-scripts/GoogleTTS_demo.sh`, `pico2text_demo.sh` — should be deleted.
- `ollama/` — should be deleted.
- `demo/` — not reviewed; check whether it pulls in `flask-socketio`/`eventlet`,
  which are no longer in `requirements.txt`.

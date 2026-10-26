# -*- coding: utf-8 -*-
"""Speech-to-text transcription for course videos.
Usage: python transcribe.py <video> <outdir> [model]
Writes <outdir>/<video-basename>.txt with timestamped lines, and a plain
no-timestamp variant <video-basename>.plain.txt for corpus use.
"""
import os
import re
import sys
import glob
import json
import site
import time

# Make cuDNN/cuBLAS DLLs visible on Windows GPU setups.
# uv run --with puts nvidia wheels on sys.path (uv cache archive dirs), NOT in
# site.getsitepackages(), so scan sys.path first, then site-packages as fallback.
import sys

search_roots = [p for p in sys.path if p and os.path.isdir(p)]
search_roots += site.getsitepackages()
search_roots.append(site.getusersitepackages())
for sp in search_roots:
    for d in glob.glob(os.path.join(sp, "nvidia", "*", "bin")):
        d = os.path.abspath(d)
        try:
            os.add_dll_directory(d)
        except OSError:
            pass
        # CTranslate2 resolves cublas64_12.dll via the plain PATH search too
        os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")

from faster_whisper import WhisperModel


def fmt_ts(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def main():
    video = sys.argv[1]
    outdir = sys.argv[2]
    model_size = sys.argv[3] if len(sys.argv) > 3 else "large-v3-turbo"
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(video))[0]

    t0 = time.time()
    try:
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        device = "cuda"
    except Exception as e:
        print(f"[warn] CUDA unavailable ({e}); falling back to CPU int8", flush=True)
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        device = "cpu"

    segments, info = model.transcribe(
        video,
        language="zh",
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 700},
        condition_on_previous_text=False,  # stop hallucination loops
    )

    lines = []
    plain = []
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        lines.append(f"[{fmt_ts(seg.start)} -> {fmt_ts(seg.end)}] {text}")
        plain.append(text)
        print(f"[{fmt_ts(seg.start)}] {text}", flush=True)

    txt_path = os.path.join(outdir, base + ".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    plain_path = os.path.join(outdir, base + ".plain.txt")
    with open(plain_path, "w", encoding="utf-8") as f:
        f.write("".join(plain) + "\n")

    meta = {
        "video": video,
        "duration_sec": info.duration,
        "language": info.language,
        "language_probability": info.language_probability,
        "model": model_size,
        "device": device,
        "segments": len(lines),
        "elapsed_sec": round(time.time() - t0, 1),
    }
    with open(os.path.join(outdir, base + ".meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()

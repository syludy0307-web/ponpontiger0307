import json, sys
from faster_whisper import WhisperModel

AUDIO = "audio16k.wav"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "large-v3"

print(f"loading model: {MODEL}", flush=True)
model = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=4)

segments, info = model.transcribe(
    AUDIO,
    language="ja",
    task="transcribe",
    beam_size=5,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=400),
    word_timestamps=True,
    condition_on_previous_text=False,
)

print(f"detected lang={info.language} prob={info.language_probability:.3f} dur={info.duration:.2f}", flush=True)

out = []
for s in segments:
    rec = {
        "start": round(s.start, 2),
        "end": round(s.end, 2),
        "text": s.text.strip(),
        "words": [{"w": w.word, "s": round(w.start, 2), "e": round(w.end, 2), "p": round(w.probability, 3)} for w in (s.words or [])],
    }
    out.append(rec)
    print(f"[{rec['start']:6.2f} -> {rec['end']:6.2f}] {rec['text']}", flush=True)

with open(f"transcript_{MODEL}.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("DONE", flush=True)

#!/usr/bin/env python3
"""Zet de woorden uit de beheer-app (Claude-artifact) om naar de website.

Gebruik: python3 sync_from_artifact.py <export-map> <assets-map> <site-map>
<export-map>: ArtifactData-export met words/<id>.json, audio/<id>.json en settings/app.json
<assets-map>: gedownloade assets (foto's en filmpjes), bestandsnaam begint met het asset-id
Schrijft <site-map>/woorden.json en <site-map>/media/*.
"""
import base64, json, re, shutil, subprocess, sys, pathlib

exp, assets, site = map(pathlib.Path, sys.argv[1:4])
media = site / "media"
media.mkdir(parents=True, exist_ok=True)
keep, words = set(), []

def body(p):
    d = json.loads(p.read_text(encoding="utf-8"))
    return d.get("data", d) if isinstance(d.get("data"), dict) else d

for f in sorted((exp / "words").glob("*.json")):
    w = body(f)
    wid = w.get("id") or f.stem
    rec = {k: w.get(k, "") for k in ("word", "article", "theme", "sentence")}
    rec["id"], rec["createdAt"] = wid, w.get("createdAt", 0)
    img_id = w.get("imageId")
    if img_id:
        hits = list(assets.glob(img_id + "*"))
        if hits:
            name = f"{wid}.jpg"
            shutil.copyfile(hits[0], media / name)
            rec["image"] = "media/" + name; keep.add(name)
    vid_id = w.get("videoId")
    if vid_id:
        hits = list(assets.glob(vid_id + "*"))
        if hits:
            name = wid + (hits[0].suffix or ".mp4")
            # snel starten met afspelen: zet de index vooraan (zonder hercodering), anders gewoon kopiëren
            if shutil.which("ffmpeg") and subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(hits[0]), "-c", "copy", "-movflags", "+faststart", str(media / name)]).returncode == 0:
                pass
            else:
                shutil.copyfile(hits[0], media / name)
            rec["video"] = "media/" + name; rec["hasVideo"] = True; keep.add(name)
    a = exp / "audio" / f"{wid}.json"
    if w.get("hasAudio") and a.exists():
        m = re.match(r"data:([^;]+);base64,(.*)", body(a).get("data", ""), re.S)
        if m:
            ext = {"audio/mp4": "m4a", "audio/x-m4a": "m4a", "audio/mpeg": "mp3", "audio/webm": "webm", "audio/ogg": "ogg", "audio/wav": "wav", "audio/x-wav": "wav", "audio/aac": "aac", "audio/3gpp": "3gp", "audio/amr": "amr"}.get(m.group(1), "audio")
            name = f"{wid}.{ext}"
            (media / name).write_bytes(base64.b64decode(m.group(2)))
            rec["audio"] = "media/" + name; rec["hasAudio"] = True; keep.add(name)
    if rec["word"]:
        words.append(rec)

for f in media.iterdir():
    if f.name not in keep:
        f.unlink()
hidden = []
s = exp / "settings" / "app.json"
if s.exists():
    hidden = body(s).get("hiddenStarters", []) or []
(site / "woorden.json").write_text(json.dumps({"words": words, "hiddenStarters": hidden}, indent=2, ensure_ascii=False), encoding="utf-8")
print(len(words), "woorden,", len(keep), "mediabestanden")

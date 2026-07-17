import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ts_path = ROOT / "frontend" / "src" / "lib" / "formLabelTranslations.ts"
ts = ts_path.read_text(encoding="utf-8")

start = ts.index("const PHRASES")
body = ts[start : ts.index("};", start)]
keys = set(re.findall(r'\n\s*"((?:[^"\\]|\\.)*)":', body))
keys = {k.encode().decode("unicode_escape") for k in keys}
print("dictionary has", len(keys), "entries")

missing: Counter = Counter()
total_segments = 0
covered_segments = 0

for form in ["i-130", "i-765", "g-28"]:
    data = json.loads(
        (ROOT / "backend" / "app" / "seed_data" / "field_inventories" / f"{form}.json").read_text(
            encoding="utf-8"
        )
    )
    for e in data:
        segments = re.split(r"(?<=[.])\s+", e["label"])
        for seg in segments:
            s = seg.strip()
            if not s:
                continue
            if re.fullmatch(r"[A-Za-z]\.|\d+\.", s):
                continue  # line numbers / item letters need no translation
            total_segments += 1
            if s in keys or re.fullmatch(r"through\s+\d+\.", s, re.IGNORECASE):
                covered_segments += 1
            else:
                missing[s] += 1

print(f"coverage: {covered_segments}/{total_segments} segments ({covered_segments / total_segments:.1%})")
print()
print("TOP MISSING SEGMENTS:")
for seg, count in missing.most_common(120):
    print(count, "|", seg)

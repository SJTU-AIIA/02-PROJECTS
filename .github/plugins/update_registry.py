import json, os, glob
from datetime import datetime, timezone, timedelta

utc_8 = timezone(timedelta(hours=8))

registry = {"projects": []}
for manifest in glob.glob("projects/**/manifest.json"):
    with open(manifest) as f:
        data = json.load(f)
        data["path"] = os.path.dirname(manifest)
        # Add last_updated timestamp
        data["last_updated"] = datetime.now(utc_8).isoformat()
        if data["created"] == "":
            data["created"] = data["last_updated"]
        registry["projects"].append(data)

with open("projects/_registry.json", "w") as f:
    json.dump(registry, f, indent=2, sort_keys=True)
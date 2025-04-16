import json, os, glob, sys
from datetime import datetime, timezone, timedelta

def update_registry():
    """
    Keeps a registry.json file to keep track of all projects.
    """
    utc_8 = timezone(timedelta(hours=8))

    registry = {"projects": []}
    for manifest in glob.glob("projects/**/manifest.json"):
        with open(f"projects/{manifest}/manifest.json") as f:
            data = json.load(f)
            data["path"] = os.path.dirname(manifest)
            # Add last_updated timestamp
            data["last_updated"] = datetime.now(utc_8).isoformat()
            if data["created"] == "":
                data["created"] = data["last_updated"]
            registry["projects"].append(data)

    with open("projects/_registry.json", "w") as f:
        json.dump(registry, f, indent=2, sort_keys=True)

if __name__ == "__main__":
    update_registry()
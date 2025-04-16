import json, os, glob, sys
from datetime import datetime, timezone, timedelta
from baselib import ROOT_DIR # note: we are NOT in the root directory. Add ROOT_DIR in front of paths to access the whole repo.

def update_registry():
    """
    Keeps a registry.json file to keep track of all projects.
    """
    utc_8 = timezone(timedelta(hours=8))

    registry = {"projects": []}
    for manifest in glob.glob(os.path.join(str(ROOT_DIR),"projects/**/manifest.json")):
        with open(manifest) as f:
            data = json.load(f)
            data["path"] = os.path.dirname(manifest)
            # Add last_updated timestamp
            data["last_updated"] = datetime.now(utc_8).isoformat()
            if data["created"] == "":
                data["created"] = data["last_updated"]
            registry["projects"].append(data)

    with open(ROOT_DIR / "projects/_registry.json", "w") as f:
        json.dump(registry, f, indent=2, sort_keys=True)

if __name__ == "__main__":
    update_registry()
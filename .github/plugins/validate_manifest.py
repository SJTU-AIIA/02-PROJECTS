import json, jsonschema, sys, os
from baselib import ROOT_DIR  # note: we are NOT in the root directory. Add ROOT_DIR in front of paths to access the whole repo.

schema = {
    "type": "object",
    "required": ["name", "datetime", "author", "tags"],
    "properties": {
        "name": {"type": "string"},
        "datetime": {"type": "string", "format": "date-time"}, # ISO 8601
        "author": {"type": "array"},
        "tags": {"type": "array"}
    }
}

def validate(manifest_path, author):
    manifest_path = ROOT_DIR / manifest_path
    try:
        with open(manifest_path) as f:
            data = json.load(f)
            jsonschema.validate(data, schema) # validates format
        data["author"] = [author]
        with open(manifest_path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)   # adds author information directly
        sys.exit(0)
    except FileNotFoundError:
        sys.exit(3)

if __name__ == "__main__":
    validate(sys.argv[1], sys.argv[2])
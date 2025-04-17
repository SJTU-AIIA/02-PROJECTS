import json, jsonschema, sys, os
from baselib import ROOT_DIR  # note: we are NOT in the root directory. Add ROOT_DIR in front of paths to access the whole repo.

schema = {
    "type": "object",
    "required": ["name", "created", "tags", "image", "version"],
    "properties": {
        "name": {"type": "string"},
        "created": {"type": "string", "format": "date-time"}, # ISO 8601
        "tags": {"type": "array"},
        "image": {"type": "string"},
        "version": {"type": "string"},
        "ports": {
            "type": "object",
            "patternProperties": {
                "^\\d+:\\d+$": {"type": "string"},
            },
        }
    }
}    
# Note: the schema is not complete. It only checks for the required fields and their types.

def validate(manifest_path, author):
    manifest_path = ROOT_DIR / manifest_path

    try:
        with open(manifest_path) as f:
            data = json.load(f)
            jsonschema.validate(data, schema) # validates format
        data["authors"] = [author]
        with open(manifest_path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)   # adds author information directly
        sys.exit(0)
    except FileNotFoundError:
        sys.exit(3)

if __name__ == "__main__":
    validate(sys.argv[1], sys.argv[2])
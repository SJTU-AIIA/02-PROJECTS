import json, jsonschema, sys

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
    with open(manifest_path) as f:
        data = json.load(f)
        jsonschema.validate(data, schema) # validates format
    data["author"] = [author]
    with open(manifest_path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)   # adds author information directly

if __name__ == "__main__":
    validate(sys.argv[1], sys.argv[2])
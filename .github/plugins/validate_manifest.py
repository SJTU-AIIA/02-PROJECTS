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

def validate(manifest_path):
    with open(manifest_path) as f:
        data = json.load(f)
    jsonschema.validate(data, schema)

if __name__ == "__main__":
    validate(sys.argv[1])
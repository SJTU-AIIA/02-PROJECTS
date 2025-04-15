# PROJECTS PANEL
## Instructions
### 1. Copy Template:
```bash
cp -r projects/.template projects/my_project
```
### 2. Edit `manifest.json`:
```json
{
  "name": "My Project",
  "authors": ["@alice", "@bob"],
  "created": "2023-08-25T09:30:00Z",
  "license": "MIT",
  "tags": ["llm", "chatbot"]
}
```
### 3. Submit:
```bash
git checkout -b my-project
git add projects/my_project
git commit -m "Add my_project"
git push origin my-project
```
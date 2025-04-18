import json
from pathlib import Path

def generate_markdown(registry_path):
    with open(registry_path) as f:
        data = json.load(f)
    
    md_content = """# Project Registry

| Project | Authors | Version | Tags | Last Updated | Links |
|---------|---------|---------|------|--------------|-------|
"""
    for project in data["projects"]:
        authors = ", ".join(f"@{a}" for a in project["authors"])
        tags = ", ".join(f"`{t}`" for t in project["tags"])
        md_content += f"| {project['name']} | {authors} | {project['version']} | {tags} | {project['last_updated'][:10]} | [Folder]({project['path']}) \| [Image]({project['image']}) |\n"

    # Add search functionality
    md_content += """
<script>
document.addEventListener('DOMContentLoaded', function() {
    const table = document.querySelector('table');
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Search projects...';
    input.style.marginBottom = '10px';
    input.style.width = '100%';
    input.style.padding = '8px';
    table.parentNode.insertBefore(input, table);

    input.addEventListener('keyup', function() {
        const filter = input.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(filter) ? '' : 'none';
        });
    });
});
</script>
"""
    return md_content

if __name__ == "__main__":
    registry_path = Path("projects/_registry.json")
    md_path = Path("projects/REGISTRY.md")
    
    md_content = generate_markdown(registry_path)
    md_path.write_text(md_content)
    print(f"Generated {md_path}")
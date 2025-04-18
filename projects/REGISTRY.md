# Project Registry

| Project | Authors | Version | Tags | Last Updated | Links |
|---------|---------|---------|------|--------------|-------|
| test2 | @DysonFabienSun | 0.0.0 |  | 2025-04-18 | [Folder](/home/runner/work/02-PROJECTS/02-PROJECTS/projects/test2) \| [Image]() |
| dfs-rag-streamlit-demo | @DysonFabienSun | 6.0.0 | `rag`, `streamlit`, `llm` | 2025-04-18 | [Folder](/home/runner/work/02-PROJECTS/02-PROJECTS/projects/dfs-rag-streamlit-demo) \| [Image](ghcr.io/sjtu-aiia/dfs-rag-streamlit-demo:6.0.0) |

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

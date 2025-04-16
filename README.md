# PROJECTS PANEL
## Usage of AIIA-CLI (PROJ-CLI) for Project Management
### Create New Project:
Make sure your command window is in the ROOT of the repo.
```bash
proj-cli new project_name [--port [8000:8000] --env ENV_1=123 --env ENV_2=456]
```
This creates a project in the /projects pile with a specified port and specified default environment variables. The port defaults at `[8000:8000]` (inbound and outbound docker ports) and this should be left untouched. Default environment variables will be applied when running the docker build.

A prompt will be returned upon successful insertion.

### (Alternative) Format Project Folder:
If you have already ported in the project folder yet want to format to the template, there is a neat function to do just that!
```bash
proj-cli format project_name [--port [8000:8000] --env ENV_1=123 --env ENV_2=456]
```
This adds all files in the template into your project folder. All conflicting files will be highlighted and you will be given the option to keep or overwrite the original file. README.md is given an option to merge or keep as is. Default port and env variables will be applied when running the docker build.

A prompt will be returned upon successful insertion.

### (Alternative) Import from Repository:
If you want to import a project from another repo you personally have, this function allows a project to be imported while keeping our specifications.
```bash
proj-cli import_repo repo_url [--port [8000:8000] --env ENV_1=123 --env ENV_2=456 --branch branch]
```
This will import a repository of your choosing. Branch defaults to main. All templates will be automatically generated.

A prompt will be returned upon successful insertion.

### Submit & Commit Project:
Make sure you have CD'ed into the project folder, as in `/projects/your_project/`.
```bash
proj-cli submit message
```
This will commit and push the project, and log the message field into the system.

### Deploy Docker Build to GHCR:
Ensure the Dockerfile exists and is configured.
```bash
proj-cli deploy [--bump major/minor/patch]
```
This will build a new version 

### Run Docker Build:
Ensure you already have the Docker package built, deployed to GHCR and are in your own project folder.
```bash
proj-cli run [--version latest --port [8000:8000] --env ENV1=123 --env ENV2=456]
```
This will run the version as dictated. If version is latest or the field isn't filled in, the latest version of the build will be run. The port and env fields can be omitted and will use default values dictated when creating the project.

## Manual Alternative:

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
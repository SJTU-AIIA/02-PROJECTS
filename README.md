# PROJECTS PANEL
## Usage of AIIA-CLI for Project Management
Enables much easier use of certain key functions in the projects repo. Developed and maintained by SJTU-AIIA.

To use:
### Install:
```bash
pip install aiia-cli
```

**IMPORTANT NOTE:** Even though the module is called aiia-cli, the main cli interface is operated via the command `proj-cli`.

### Create New Project:
Make sure your command window is in the ROOT of the repo.
```bash
proj-cli new project_name [--port [8000:8000] --env ENV_1=123 --env ENV_2=456]
```
This creates a project in the /projects pile with a specified port and specified default environment variables. The port defaults at `[8000:8000]` (inbound and outbound docker ports) and this should be left untouched. Default environment variables will be applied when running the docker build.

A prompt will be returned upon successful insertion.

### Submit & Commit Project:
Make sure you have CD'ed into the project folder, as in `/projects/your_project/`.
```bash
proj-cli submit message
```
This will commit and push the project, and log the message field into the system.

### Build Docker file:
Ensure you have CD'ed into the project folder, and have a Dockerfile configured up, along with the requirements.txt and any associated files.
```bash
proj-cli build build_name
```
This will build a Docker package as precised by the Dockerfile, returning a build under the build_name, that you can run with the `proj-cli run` command.

### Run Docker Build:
Ensure you already have the Docker package built and are in your own project folder.
```bash
proj-cli run build_name [--port [8000:8000] --env ENV1=123 --env ENV2=456]
```
This will run the build under the build_name. The port and env fields can be omitted and will use default values dictated under the `proj-cli new` command.

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
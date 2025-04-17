# PROJECTS PANEL
Welcome to our projects manager! This is where all projects are tracked. For a starter's guide to how you can contribute, read the example below.
## Sample AIIA-CLI (PROJ-CLI) Workflow:
### First Steps
Install AIIA-CLI. This is a proprietary, custom tool written from scratch to facilitate projects creation and management.
```bash
pip install --upgrade aiia-cli
```
Then, navigate to the `02-PROJECTS` repository, and open a command line at the root of the file.
### If you already have a repo with your project:
```bash
proj-cli import-repo <your_repo_url> [OPTION] --port 8000:8000 --env ENV_1=123 --env ENV_2=456 --branch branch
```

### Alternatively, if you want to start anew:
```bash
proj-cli new project_name [OPTION] --port 8000:8000 --env ENV_1=123 --env ENV_2=456
```

### If you already made a project folder, please use the format function to format the project folder with our requirements:

```bash
proj-cli format project_name [OPTION] --port 8000:8000 --env ENV_1=123 --env ENV_2=456
```

Default port and build environment variables could be provided here. (optional: default ports will be set to 8000:8000, branch (if import_repo) to `main`, and env left empty)
This will create a project folder, and after a small delay, please refresh your github repo and manage your new manifest and README files.

Should a login be prompted, run `proj-cli login` and enter your PAT (Personal Access Token), accessible through Github settings > Developer Settings > Personal Access Tokens. **The fields `repo` and `write:packages` (`read:packages`) must be selected in this PAT.** This will be useful when authenticating with GHCR.

### Building Sample Project
After filling up your project, the next step will be to build and deploy it on GHCR, github's Docker image platform. Ensure you have docker Desktop (or alternatives) installed and you have access to the `docker` suite of commands. `proj-cli` offers a few versatile functions for deployment, and the process goes as follows:

```bash
cd projects/<your project name>
proj-cli login
proj-cli deploy --bump major  # deploys my new Docker image, with a new major version update
proj-cli run
```

Voilà! Test out your new project!

For more detailed instructions, check the docs below.

## Docs of AIIA-CLI (PROJ-CLI) for Project Management
### Create New Project:
Make sure your command window is in the ROOT of the repo.
```bash
proj-cli new project_name [OPTION] --port 8000:8000 --env ENV_1=123 --env ENV_2=456
```
This creates a project in the /projects pile with a specified port and specified default environment variables. The port defaults at `8000:8000` (inbound and outbound docker ports) and this should be left untouched. Default environment variables will be applied when running the docker build.

A prompt will be returned upon successful insertion.

### (Alternative) Format Project Folder:
If you have already ported in the project folder yet want to format to the template, there is a neat function to do just that!
```bash
proj-cli format project_name [OPTION] --port 8000:8000 --env ENV_1=123 --env ENV_2=456
```
This adds all files in the template into your project folder. All conflicting files will be highlighted and you will be given the option to keep or overwrite the original file. README.md is given an option to merge or keep as is. Default port and env variables will be applied when running the docker build.

A prompt will be returned upon successful insertion.

### (Alternative) Import from Repository:
If you want to import a project from another repo you personally have, this function allows a project to be imported while keeping our specifications.
```bash
proj-cli import-repo repo-url [OPTION] --rename newname --port 8000:8000 --env ENV_1=123 --env ENV_2=456 --branch branch
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
proj-cli deploy [OPTION] --bump major/minor/patch
```
This will build a new version 

### Run Docker Build:
Ensure you already have the Docker package built, deployed to GHCR and are in your own project folder.
```bash
proj-cli run [OPTION] --version latest --port [8000:8000] --env ENV1=123 --env ENV2=456
```
This will run the version as dictated. If version is latest or the field isn't filled in, the latest version of the build will be run. The port and env fields can be omitted and will use default values dictated when creating the project.
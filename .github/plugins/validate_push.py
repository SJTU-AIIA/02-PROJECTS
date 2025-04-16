import os
import sys
import json
from git import Repo
from baselib import ROOT_DIR

def validate_PR(pr_author):
    # this assumes the pr_author aka visitor is NOT an admin
    repo = Repo(".")
    modified_files = [diff.a_path for diff in repo.head.commit.diff()]

    for file_path in modified_files:
        # Get the project folder (e.g., /projects/project1/file.txt → project1)
        project_folder = file_path.split("/")[1]  # Adjust based on your structure
        manifest_path = ROOT_DIR / f"projects/{project_folder}/manifest.json"

        if not os.path.exists(manifest_path):
            print(f"Manifest not found in {project_folder}")
            sys.exit(1)

        with open(manifest_path, "r") as f:
            manifest = json.load(f)
            allowed = manifest["authors"]

            if pr_author not in allowed:
                print(f"{pr_author} not allowed to modify {project_folder}")
                sys.exit(1)

    print("All changes are authorized!")
    sys.exit(0)

if __name__ == "__main__":
    validate_PR(sys.argv[1])

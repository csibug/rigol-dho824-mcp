import os


def list_project_structure(target_folder='.'):
    """
    Lists the directory tree starting from the project root.
    Excludes python cache, hidden files, and virtual environments.
    """
    if not os.path.exists(target_folder):
        print(f"Directory '{target_folder}' not found.")
        return

    # Kiszűrjük a zavaró tényezőket (venv, git, cache)
    exclude_dirs = {'.git', '__pycache__', '.pytest_cache', '.venv', 'venv', '.ruff_cache', '.mypy_cache'}

    print(f"{os.path.abspath(target_folder)}/")

    for root, dirs, files in os.walk(target_folder):
        # In-place szűrés a walk-hoz
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

        level = os.path.relpath(root, target_folder).count(os.sep)
        if root == target_folder:
            indent = ""
        else:
            indent = "    " * (level + 1)
            print(f"{indent}{os.path.basename(root)}/")

        subindent = "    " * (level + 2)
        for f in files:
            if not f.startswith(('.', '__')):
                print(f"{subindent}{f}")

if __name__ == "__main__":
    # Most már a gyökérből indítjuk!
    list_project_structure('.')

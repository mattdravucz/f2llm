import os
import argparse
import sys
import re
import json
import pathspec


def load_gitignore_spec(gitignore_path):
    if not os.path.exists(gitignore_path):
        return None

    with open(gitignore_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def parse_folder_to_json(input_folder, output_file, spec):
    """Parse folder structure into JSON format."""
    output = {"files": []}
    for root, dirs, files in os.walk(input_folder):
        rel_root = os.path.relpath(root, input_folder)
        if rel_root == ".":
            rel_root = ""

        dirs[:] = [
            d for d in dirs
            if not (spec and spec.match_file(os.path.normpath(os.path.join(rel_root, d))))
        ]

        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.normpath(os.path.join(rel_root, file))

            if os.path.abspath(file_path) == os.path.abspath(output_file):
                continue
            if spec and spec.match_file(relative_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as in_file:
                    content = in_file.read()
            except Exception as e:
                content = f"Error reading file: {str(e)}"

            # wrap with code fences
            ext = os.path.splitext(file)[1].lstrip('.')
            lang = ext if ext else ''
            wrapped_content = f"```{lang}\n{content}\n```"

            output["files"].append({
                "file_path": relative_path,
                "notes": "",
                "content": wrapped_content,
            })

    with open(output_file, "w", encoding="utf-8") as out_file:
        json.dump(output, out_file, indent=2)

    print(f"Parsing complete. JSON written to {output_file}")


def apply_changes_from_json(input_file, repo_folder):
    """Apply changes described in a JSON file with the schema."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle moved files
    for move_info in data.get('moved_files', []):
        old_path = os.path.join(repo_folder, move_info['old_path'])
        new_path = os.path.join(repo_folder, move_info['new_path'])
        
        if os.path.exists(old_path):
            # Create directory for new path if needed
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            # Move the file
            os.rename(old_path, new_path)
            print(f"Moved: {move_info['old_path']} -> {move_info['new_path']}")

    # Handle deleted files
    for file_info in data.get('deleted_files', []):
        if isinstance(file_info, dict):
            rel_path = file_info['file_path']
        else:
            # Handle legacy format where deleted_files was array of strings
            rel_path = file_info
            
        full_path = os.path.join(repo_folder, rel_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"Deleted: {rel_path}")

    # Handle modified and added files
    for section in ('modified_files', 'added_files'):
        for file_info in data.get(section, []):
            rel_path = file_info['file_path']
            content = file_info['content']
            
            # unwrap code fences if present
            m = re.search(r"```(?:\w+)?\n(.*?)\n```", content, flags=re.DOTALL)
            if m:
                content = m.group(1)

            full_path = os.path.join(repo_folder, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as out_file:
                out_file.write(content)
            print(f"Written: {rel_path} ({section})")

    print("Apply complete.")


def main():
    parser = argparse.ArgumentParser(
        description="F2LLM - Parse folder to JSON or apply JSON changes to folder."
    )
    parser.add_argument(
        "input",
        help="Input folder (for parsing) or JSON file (for applying changes)."
    )
    parser.add_argument(
        "output", 
        help="Output JSON file (for parsing) or target folder (for applying changes)."
    )
    parser.add_argument(
        "--apply",
        action="store_true", 
        help="Apply changes from JSON to folder instead of parsing folder to JSON."
    )

    args = parser.parse_args()

    if args.apply:
        # Apply mode: input is JSON file, output is target folder
        if not os.path.isfile(args.input):
            print(f"Error: {args.input} is not a valid file.")
            sys.exit(1)
        if not os.path.isdir(args.output):
            print(f"Error: {args.output} is not a valid directory.")
            sys.exit(1)
        apply_changes_from_json(args.input, args.output)
    else:
        # Parse mode: input is folder, output is JSON file
        if not os.path.isdir(args.input):
            print(f"Error: {args.input} is not a valid directory.")
            sys.exit(1)

        gitignore_path = os.path.join(args.input, ".gitignore")
        spec = load_gitignore_spec(gitignore_path)
        parse_folder_to_json(args.input, args.output, spec)


if __name__ == "__main__":
    main()
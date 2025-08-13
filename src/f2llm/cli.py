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


def generate_folder_from_json(input_file, output_folder):
    """Generate folder structure from JSON format (reverse of parse)."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    for file_info in data.get('files', []):
        rel_path = file_info['file_path']
        content = file_info['content']
        
        # unwrap code fences if present
        m = re.search(r"```(?:\w+)?\n(.*?)\n```", content, flags=re.DOTALL)
        if m:
            content = m.group(1)

        full_path = os.path.join(output_folder, rel_path)
        
        # Create directory structure if needed
        dir_path = os.path.dirname(full_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # Write the file
        with open(full_path, 'w', encoding='utf-8') as out_file:
            out_file.write(content)
        
        print(f"Generated: {rel_path}")

    print(f"Generation complete. Folder structure created in {output_folder}")


def apply_changes_from_json(input_file, repo_folder):
    """Apply changes described in a JSON file with the simplified schema."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle deleted files (now just strings)
    for rel_path in data.get('deleted_files', []):
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

    # Note: unchanged_files are listed but no action needed
    unchanged_count = len(data.get('unchanged_files', []))
    if unchanged_count > 0:
        print(f"Unchanged files: {unchanged_count}")

    print("Apply complete.")


def main():
    parser = argparse.ArgumentParser(
        description="F2LLM - Parse folder to JSON, generate folder from JSON, or apply JSON changes to folder."
    )
    parser.add_argument(
        "input",
        help="Input folder (for parsing), JSON file (for generating/applying changes)."
    )
    parser.add_argument(
        "output", 
        help="Output JSON file (for parsing) or target folder (for generating/applying changes)."
    )
    parser.add_argument(
        "--apply",
        action="store_true", 
        help="Apply changes from JSON to folder (expects change-based JSON schema)."
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate folder structure from JSON (reverse of parse operation)."
    )

    args = parser.parse_args()

    # Check for conflicting options
    if args.apply and args.generate:
        print("Error: Cannot use --apply and --generate together.")
        sys.exit(1)

    if args.apply:
        # Apply mode: input is JSON file, output is target folder
        if not os.path.isfile(args.input):
            print(f"Error: {args.input} is not a valid file.")
            sys.exit(1)
        if not os.path.isdir(args.output):
            print(f"Error: {args.output} is not a valid directory.")
            sys.exit(1)
        apply_changes_from_json(args.input, args.output)
    elif args.generate:
        # Generate mode: input is JSON file, output is target folder
        if not os.path.isfile(args.input):
            print(f"Error: {args.input} is not a valid file.")
            sys.exit(1)
        generate_folder_from_json(args.input, args.output)
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
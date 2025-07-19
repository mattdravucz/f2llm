import os
import argparse
import sys
import re
import json
import pathspec

MARKER = "//F2LLM//"


def load_gitignore_spec(gitignore_path):
    if not os.path.exists(gitignore_path):
        return None

    with open(gitignore_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def parse_folder_to_txt(input_folder, output_file, spec):
    output_file = os.path.abspath(output_file)

    with open(output_file, "w", encoding="utf-8") as out_file:
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

                if os.path.abspath(file_path) == output_file:
                    continue
                if spec and spec.match_file(relative_path):
                    continue

                out_file.write(f"{MARKER} {relative_path}\n")

                try:
                    with open(file_path, "r", encoding="utf-8") as in_file:
                        out_file.write(in_file.read())
                except Exception as e:
                    out_file.write(f"Error reading file: {str(e)}")

                out_file.write("\n")


def parse_folder_to_json(input_folder, output_file, spec):
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

            # Infer language from extension
            ext = os.path.splitext(file)[1].lstrip(".")
            lang = ext if ext else ""
            wrapped_content = f"```{lang}\n{content}\n```"

            output["files"].append({
                "file_path": relative_path,
                "notes": "",
                "content": wrapped_content,
            })

    with open(output_file, "w", encoding="utf-8") as out_file:
        json.dump(output, out_file, indent=2)

    print(f"Parsing complete. JSON written to {output_file}")


def generate_files_from_txt(input_file, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as in_file:
        content = in_file.read()

    file_sections = re.split(
        rf"^{re.escape(MARKER)} (.+)$", content, flags=re.MULTILINE
    )

    for i in range(1, len(file_sections), 2):
        relative_path = file_sections[i].strip()
        file_content = file_sections[i + 1].lstrip("\n")

        full_path = os.path.join(output_folder, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as out_file:
            out_file.write(file_content)

    print(f"Files generated in {output_folder}")


def generate_files_from_json(input_file, output_folder):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for file_info in data.get("files", []):
        path = os.path.join(output_folder, file_info["file_path"])
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Extract content inside triple backticks if present
        content = file_info["content"]
        match = re.search(r"```(?:\w+)?\n(.*?)\n```", content, flags=re.DOTALL)
        if match:
            content = match.group(1)

        with open(path, "w", encoding="utf-8") as out_file:
            out_file.write(content)

    print(f"Files generated in {output_folder}")


def main():
    parser = argparse.ArgumentParser(
        description="Parse files to prompt format or generate files from a prompt definition."
    )
    parser.add_argument(
        "input",
        help="Input folder path (for parsing) or input file path (for generation).",
    )
    parser.add_argument(
        "output",
        help="Output file path (for parsing) or output folder path (for generation).",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate files from parsed content instead of parsing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Use JSON format instead of plain text markers.",
    )

    args = parser.parse_args()

    if args.generate:
        if not os.path.isfile(args.input):
            print(f"Error: {args.input} is not a valid file.")
            sys.exit(1)

        if args.json:
            generate_files_from_json(args.input, args.output)
        else:
            generate_files_from_txt(args.input, args.output)
    else:
        if not os.path.isdir(args.input):
            print(f"Error: {args.input} is not a valid directory.")
            sys.exit(1)

        gitignore_path = os.path.join(args.input, ".gitignore")
        spec = load_gitignore_spec(gitignore_path)

        if args.json:
            parse_folder_to_json(args.input, args.output, spec)
        else:
            parse_folder_to_txt(args.input, args.output, spec)

        print(f"Parsing complete. Output written to {args.output}")


if __name__ == "__main__":
    main()

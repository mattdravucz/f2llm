import os
import argparse
import sys
import fnmatch
import re

def parse_gitignore(gitignore_path):
    ignore_patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ignore_patterns.append(line)
    
    # Always ignore .git directory
    ignore_patterns.append('.git/')
    
    return ignore_patterns

def should_ignore(path, ignore_patterns):
    path_parts = path.split(os.sep)
    for pattern in ignore_patterns:
        if pattern.endswith('/'):
            if any(fnmatch.fnmatch(part, pattern[:-1]) for part in path_parts):
                return True
        elif '/' in pattern:
            if fnmatch.fnmatch(path, pattern):
                return True
        else:
            if fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
    return False

def parse_folder(input_folder, output_file):
    output_file = os.path.abspath(output_file)
    gitignore_path = os.path.join(input_folder, '.gitignore')
    ignore_patterns = parse_gitignore(gitignore_path)

    with open(output_file, 'w', encoding='utf-8') as out_file:
        for root, dirs, files in os.walk(input_folder):
            # Use list() to create a copy of dirs, so we can modify it
            for dir in list(dirs):
                if should_ignore(os.path.relpath(os.path.join(root, dir), input_folder), ignore_patterns):
                    dirs.remove(dir)
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, input_folder)
                
                if os.path.abspath(file_path) == output_file:
                    continue
                
                if should_ignore(relative_path, ignore_patterns):
                    continue
                
                out_file.write(f"{'='*40}\n")
                out_file.write(f"File: {relative_path}\n")
                out_file.write(f"{'='*40}\n")
                out_file.write("Content:\n")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as in_file:
                        content = in_file.read()
                        out_file.write(content)
                except Exception as e:
                    out_file.write(f"Error reading file: {str(e)}\n")
                
                out_file.write(f"\n\n{'#'*40}\n\n")

def generate_files(input_file, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    
    with open(input_file, 'r', encoding='utf-8') as in_file:
        content = in_file.read()
    
    file_pattern = re.compile(r"={40}\nFile: (.+?)\n={40}\nContent:\n(.*?)(?:\n{2}#{40})", re.DOTALL)
    
    for match in file_pattern.finditer(content):
        relative_path, file_content = match.groups()
        full_path = os.path.join(output_folder, relative_path)
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as out_file:
            out_file.write(file_content)
    
    print(f"Files generated in {output_folder}")

def main():
    parser = argparse.ArgumentParser(description="Parse files or generate files from parsed content.")
    parser.add_argument("input", help="The input folder path (for parsing) or input file path (for generating).")
    parser.add_argument("output", help="The output file path (for parsing) or output folder path (for generating).")
    parser.add_argument("--generate", action="store_true", help="Generate files from parsed content instead of parsing.")
    
    args = parser.parse_args()
    
    if args.generate:
        if not os.path.isfile(args.input):
            print(f"Error: {args.input} is not a valid file.")
            sys.exit(1)
        generate_files(args.input, args.output)
    else:
        if not os.path.isdir(args.input):
            print(f"Error: {args.input} is not a valid directory.")
            sys.exit(1)
        parse_folder(args.input, args.output)
        print(f"Parsing complete. Output written to {args.output}")

if __name__ == "__main__":
    main()
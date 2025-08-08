# F2LLM - Folder to LLM CLI Tool

A simple command-line tool for converting folder structures to JSON format for LLM processing and applying LLM-generated changes back to your project.

## Installation

Requires Python 3.6+ and the `pathspec` library:

```bash
pip install pathspec
```

## Usage

F2LLM has two main modes:

### 1. Parse Mode (Default)
Convert a folder structure into JSON format:

```bash
python f2llm.py <folder_path> <output.json>
```

**Example:**
```bash
python f2llm.py my_project project_files.json
```

This creates a JSON file containing all files in the folder with their content wrapped in code fences.

### 2. Apply Mode
Apply LLM-generated changes from JSON back to your project:

```bash
python f2llm.py --apply <changes.json> <target_folder>
```

**Example:**
```bash
python f2llm.py --apply llm_response.json my_project
```

## JSON Schema

The tool expects/produces JSON files with this structure:

```json
{
  "modified_files": [
    {
      "file_path": "src/main.py",
      "notes": "Updated function logic",
      "content": "```python\n# file content here\n```"
    }
  ],
  "added_files": [
    {
      "file_path": "src/new_file.py", 
      "notes": "New utility module",
      "content": "```python\n# new file content\n```"
    }
  ],
  "moved_files": [
    {
      "old_path": "old/location.py",
      "new_path": "new/location.py",
      "notes": "Reorganized project structure"
    }
  ],
  "unchanged_files": [
    "README.md",
    "package.json"
  ],
  "deleted_files": [
    {
      "file_path": "obsolete_file.py",
      "notes": "No longer needed"
    }
  ]
}
```

## Features

- **Gitignore Support**: Automatically respects `.gitignore` files during parsing
- **File Operations**: Handles create, modify, move, and delete operations
- **Code Fences**: Automatically wraps file content with appropriate language syntax highlighting
- **Safe Paths**: Creates necessary directories when applying changes
- **Error Handling**: Graceful handling of file read/write errors

## Common Workflow

1. **Extract your project** for LLM analysis:
   ```bash
   python f2llm.py my_project prompt.json
   ```

2. **Send `prompt.json` to your LLM** with instructions

3. **Apply the LLM's response** back to your project:
   ```bash
   python f2llm.py --apply llm_response.json my_project
   ```

## Notes

- The tool preserves file permissions and creates directories as needed
- Binary files or files that can't be read as UTF-8 will show an error message in their content
- When moving files, the tool creates necessary parent directories automatically
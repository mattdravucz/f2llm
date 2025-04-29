# Folder to LLM Prompt

1. To parse a folder and create a text file:
   ```
   f2llm /path/to/input/folder /path/to/output/file.txt
   ```

2. To generate files from a parsed text file:
   ```
   f2llm --generate /path/to/input/file.txt /path/to/output/folder
   ```

# Install
```
   pip install f2llm
```

### Versioning

1. Create a **Git tag** at the version you want, e.g.:
    
    ```
    git tag v0.2.0
    git push origin v0.2.0
    ```
    
2. Go to **Actions ➔ Release ➔ Run workflow** in GitHub’s UI.
    
3. Select your branch (e.g. `main`) and click **Run workflow**.
    

The workflow will read the version (`v0.2.0`) via setuptools_scm, build, and upload — but **only** when you trigger it.
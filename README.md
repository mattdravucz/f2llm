# Folder to LLM Prompt

1. To parse a folder and create a text file:
   ```
   f2llm /path/to/input/folder /path/to/output/file.txt
   ```

2. To generate files from a parsed text file:
   ```
   f2llm --generate /path/to/input/file.txt /path/to/output/folder
   ```


### System Prompt

When responding with file content, please format your output exactly as follows:

1. Start each file with a line of 40 equal signs (=).
2. On the next line, write "File: " followed by the relative path of the file.
3. Follow this with another line of 40 equal signs (=).
4. On the next line, write "Content:".
5. Then, on a new line, begin the actual content of the file.
6. After the file content, add two newlines, followed by a line of 40 hash signs (#).
7. Add two more newlines before starting the next file (if any).

Here's an example of the correct format:

```
'='*40
File: example/hello.py
'='*40
Content:
def hello():
    print("Hello, world!")

if __name__ == "__main__":
    hello()


'#'*40


'='*40
File: example/data/config.json
'='*40
Content:
{
    "version": "1.0",
    "debug": false,
    "api_key": "YOUR_API_KEY_HERE"
}


'#'*40
```

Please follow this format exactly for any file content you provide. This ensures that the output can be correctly processed by the f2llm tool's generate function.
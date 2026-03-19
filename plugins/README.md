# TrashClaw Plugins

Drop `.py` files in this directory to extend TrashClaw with custom tools.

## How Plugins Work

Each plugin file needs a `TOOL_DEF` dictionary and a function matching the tool name:

```python
TOOL_DEF = {
    "name": "my_tool",
    "description": "What this tool does",
    "parameters": {
        "type": "object",
        "properties": {
            "arg1": {"type": "string", "description": "First argument"}
        },
        "required": ["arg1"]
    }
}

def tool_my_tool(arg1):
    """Implementation of the tool."""
    return {"result": f"You passed: {arg1}"}
```

## Available Plugins

### project_summary
Get a quick overview of the current project structure.

**Usage:**
```
/project_summary
/project_summary path=/some/dir max_depth=5
```

**Returns:**
- Total file/directory counts
- Total size (human-readable)
- File type distribution
- Recently modified files

## Creating Your Own Plugin

1. Create a new `.py` file in this directory
2. Define `TOOL_DEF` with your tool's schema
3. Implement `tool_<name>()` function
4. Restart TrashClaw or reload plugins

## Example: Weather Plugin

```python
import requests

TOOL_DEF = {
    "name": "weather",
    "description": "Get current weather for a city",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"}
        },
        "required": ["city"]
    }
}

def tool_weather(city):
    response = requests.get(f"https://wttr.in/{city}?format=j1")
    data = response.json()
    return {
        "temp": data["current_condition"][0]["temp_C"],
        "condition": data["current_condition"][0]["weatherDesc"][0]["value"]
    }
```

## Plugin Guidelines

- Keep plugins focused and single-purpose
- Handle errors gracefully
- Return structured data (dict/list) when possible
- Document your tool with clear descriptions
- Test your plugin before sharing

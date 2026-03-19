#!/usr/bin/env python3
"""
TrashClaw Plugin: Project Summary Tool
======================================
Provides a quick overview of the current project structure.

Drop this file in ~/.trashclaw/plugins/ to enable.
"""

import os
from pathlib import Path
from collections import Counter

TOOL_DEF = {
    "name": "project_summary",
    "description": "Get a quick overview of the current project - file counts by type, total size, recent modifications",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory to analyze (default: current working directory)"
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum directory depth to scan (default: 3)",
                "default": 3
            },
            "include_hidden": {
                "type": "boolean",
                "description": "Include hidden files/directories (default: false)",
                "default": False
            }
        },
        "required": []
    }
}


def tool_project_summary(path=None, max_depth=3, include_hidden=False):
    """
    Analyze a project directory and return a summary.
    
    Args:
        path: Directory to analyze (default: CWD)
        max_depth: Maximum depth to scan
        include_hidden: Whether to include hidden files
    
    Returns:
        dict: Project summary with file counts, sizes, and structure
    """
    base_path = Path(path) if path else Path.cwd()
    
    if not base_path.exists():
        return {"error": f"Path does not exist: {base_path}"}
    
    if not base_path.is_dir():
        return {"error": f"Path is not a directory: {base_path}"}
    
    # Counters
    file_extensions = Counter()
    total_files = 0
    total_dirs = 0
    total_size = 0
    recent_files = []  # Last 10 modified
    
    # Walk the directory tree
    for root, dirs, files in os.walk(base_path):
        # Calculate depth
        depth = len(Path(root).relative_to(base_path).parts)
        if depth > max_depth:
            dirs.clear()  # Don't go deeper
            continue
        
        # Filter hidden directories
        if not include_hidden:
            dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        total_dirs += len(dirs)
        
        for filename in files:
            # Filter hidden files
            if not include_hidden and filename.startswith('.'):
                continue
            
            filepath = Path(root) / filename
            
            try:
                stat = filepath.stat()
                total_size += stat.st_size
                
                # Track extension
                ext = filepath.suffix.lower() or '(no extension)'
                file_extensions[ext] += 1
                total_files += 1
                
                # Track recent files
                recent_files.append({
                    "path": str(filepath.relative_to(base_path)),
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
            except (OSError, PermissionError):
                continue
    
    # Sort recent files by modification time
    recent_files.sort(key=lambda x: x["modified"], reverse=True)
    recent_files = recent_files[:10]  # Top 10
    
    # Convert timestamps to readable format
    for f in recent_files:
        from datetime import datetime
        f["modified"] = datetime.fromtimestamp(f["modified"]).isoformat()
    
    # Build summary
    summary = {
        "path": str(base_path),
        "total_files": total_files,
        "total_directories": total_dirs,
        "total_size_bytes": total_size,
        "total_size_human": _format_size(total_size),
        "file_types": dict(file_extensions.most_common(10)),
        "recently_modified": recent_files,
        "scan_depth": max_depth,
    }
    
    return summary


def _format_size(size_bytes):
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


# Example output when run directly
if __name__ == "__main__":
    import json
    result = tool_project_summary()
    print(json.dumps(result, indent=2))

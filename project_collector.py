#!/usr/bin/env python3.10

import argparse
import configparser
from pathlib import Path
from datetime import datetime
import os
import re


def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate project log from project directory.')
    parser.add_argument('project_dir', type=str, help='Path to project directory containing config and file list')
    parser.add_argument('-l', '--language', type=str, help='Override default language from config (optional)')
    return parser.parse_args()


def get_default_language_mappings():
    """Default file extension to language mappings."""
    return {
        # Python
        '.py': 'python',
        '.pyw': 'python',
        '.pyx': 'python',

        # Ruby
        '.rb': 'ruby',
        '.rbw': 'ruby',

        # Templates
        '.erb': 'erb',
        '.html.erb': 'erb',
        '.js.erb': 'erb',
        '.css.erb': 'erb',

        # HTML/Templates
        '.html': 'html',
        '.htm': 'html',
        '.jinja': 'html',
        '.jinja2': 'html',
        '.j2': 'html',
        '.django': 'html',

        # JavaScript
        '.js': 'javascript',
        '.jsx': 'jsx',
        '.ts': 'typescript',
        '.tsx': 'tsx',
        '.vue': 'vue',

        # CSS/Styling
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',

        # Config files
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'ini',
        '.conf': 'bash',

        # Shell
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'zsh',
        '.fish': 'fish',

        # SQL
        '.sql': 'sql',

        # Markdown/Text
        '.md': 'markdown',
        '.txt': 'text',
        '.rst': 'rst',

        # Docker
        'dockerfile': 'dockerfile',
        '.dockerfile': 'dockerfile',

        # Other
        '.xml': 'xml',
        '.csv': 'csv',
        '.log': 'text',
    }


def get_default_exclude_patterns():
    """Default patterns for files to exclude."""
    return [
        '.keep',
        '.gitkeep',
        '.DS_Store',
        'Thumbs.db',
        '.tmp',
        '.temp'
    ]


def get_default_comment_patterns():
    """Default comment patterns for different languages."""
    return {
        'python': [r'^#.*$', r'^\s*""".*?"""\s*$', r"^\s*'''.*?'''\s*$"],
        'ruby': [r'^#.*$', r'^\s*=begin.*?=end\s*$'],
        'javascript': [r'^//.*$', r'^\s*/\*.*?\*/\s*$'],
        'css': [r'^\s*/\*.*?\*/\s*$'],
        'html': [r'^\s*<!--.*?-->\s*$'],
        'sql': [r'^--.*$', r'^\s*/\*.*?\*/\s*$'],
        'bash': [r'^#.*$'],
        'yaml': [r'^#.*$'],
        'ini': [r'^[#;].*$'],
        'erb': [r'^#.*$', r'^\s*<!--.*?-->\s*$'],
    }


def read_ini_config(config_path):
    """Read and validate ini configuration file."""
    config = configparser.ConfigParser()
    config.read(config_path)

    if 'Settings' not in config:
        raise ValueError("Missing 'Settings' section in config.ini file")

    settings = config['Settings']

    # Expand ~ in paths if present
    for key in ['project_root']:
        if key in settings:
            settings[key] = os.path.expanduser(settings[key])

    return settings


def read_language_mappings(config_path):
    """Read custom language mappings from config file."""
    config = configparser.ConfigParser()
    config.read(config_path)

    # Start with default mappings
    mappings = get_default_language_mappings()

    # Override/add custom mappings if section exists
    if 'LanguageMappings' in config:
        for extension, language in config['LanguageMappings'].items():
            mappings[extension] = language

    return mappings


def read_filtering_config(config_path):
    """Read file filtering and comment cleaning configuration."""
    config = configparser.ConfigParser()
    config.read(config_path)

    # Default settings
    exclude_files = True
    clean_comments = True
    exclude_patterns = get_default_exclude_patterns()
    comment_patterns = get_default_comment_patterns()

    # Read filtering settings
    if 'Filtering' in config:
        filtering = config['Filtering']
        exclude_files = filtering.getboolean('exclude_files', True)
        clean_comments = filtering.getboolean('clean_comments', True)

    # Read custom exclude patterns
    if 'ExcludePatterns' in config:
        custom_patterns = [value for key, value in config['ExcludePatterns'].items()]
        if custom_patterns:
            exclude_patterns = custom_patterns

    # Read custom comment patterns
    if 'CommentPatterns' in config:
        for language, patterns_str in config['CommentPatterns'].items():
            # Split patterns by | or comma
            patterns = [p.strip() for p in patterns_str.replace('|', ',').split(',') if p.strip()]
            if patterns:
                comment_patterns[language] = patterns

    return {
        'exclude_files': exclude_files,
        'clean_comments': clean_comments,
        'exclude_patterns': exclude_patterns,
        'comment_patterns': comment_patterns
    }


def get_language_for_file(filepath, default_language, language_mappings):
    """Determine language for file based on extension."""
    # Convert to Path object if it isn't already
    path = Path(filepath)

    # Check for compound extensions first (like .html.erb)
    full_name = path.name.lower()
    for ext in language_mappings:
        if full_name.endswith(ext.lower()) and len(ext) > 1:  # Skip single char extensions in this pass
            return language_mappings[ext]

    # Check regular extension
    extension = path.suffix.lower()
    if extension in language_mappings:
        return language_mappings[extension]

    # Check filename without extension (for files like Dockerfile)
    filename = path.name.lower()
    if filename in language_mappings:
        return language_mappings[filename]

    # Return default language
    return default_language


def should_exclude_file(filepath, exclude_patterns):
    """Check if file should be excluded based on patterns."""
    filename = filepath.name.lower()
    return any(pattern.lower() in filename for pattern in exclude_patterns)


def clean_content(content, language, comment_patterns):
    """Remove comments from content based on language."""
    if not comment_patterns:
        return content

    # Get patterns for this language
    patterns = comment_patterns.get(language, [])
    if not patterns:
        return content

    lines = content.split('\n')
    cleaned_lines = []

    for line in lines:
        # Check if line matches any comment pattern
        is_comment = False
        for pattern in patterns:
            if re.match(pattern, line, re.MULTILINE | re.DOTALL):
                is_comment = True
                break

        # Only add non-comment lines, but preserve empty lines for readability
        if not is_comment:
            cleaned_lines.append(line)
        elif line.strip() == '':  # Keep empty lines
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def read_file_list(file_list_path):
    """Read list of files or directories from file list."""
    with open(file_list_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines() if line.strip() and not line.strip().startswith('#')]


def process_file(filepath, markdown_file, project_root, default_language, language_mappings, filtering_config):
    """Add file content to Markdown with appropriate language."""
    if not filepath.exists():
        print(f"File not found: {filepath}")
        return

    # Check if file should be excluded
    if filtering_config['exclude_files'] and should_exclude_file(filepath, filtering_config['exclude_patterns']):
        print(f"Excluded file: {filepath}")
        return

    try:
        # Determine language for this specific file
        file_language = get_language_for_file(filepath, default_language, language_mappings)

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()

            # Clean comments if enabled
            if filtering_config['clean_comments']:
                content = clean_content(content, file_language, filtering_config['comment_patterns'])

            # Skip empty files after cleaning
            if not content.strip():
                print(f"Skipped empty file after cleaning: {filepath}")
                return

            relative_path = filepath.relative_to(project_root)
            markdown_file.write(f"### {relative_path}\n```{file_language}\n{content}\n```\n\n---\n\n")
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")


def process_path(item_path, markdown_file, project_root, default_language, language_mappings, filtering_config):
    """Process file or directory."""
    # Expand ~ in path if present
    item_path_expanded = os.path.expanduser(str(item_path))

    # If path is relative, make it relative to project_root
    if not os.path.isabs(item_path_expanded):
        full_path = project_root / item_path_expanded
    else:
        full_path = Path(item_path_expanded)

    if full_path.is_dir():
        print(f"Processing directory: {full_path}")
        for file in full_path.rglob("*"):
            if file.is_file():
                process_file(file, markdown_file, project_root, default_language, language_mappings, filtering_config)
    elif full_path.is_file():
        print(f"Processing file: {full_path}")
        process_file(full_path, markdown_file, project_root, default_language, language_mappings, filtering_config)
    else:
        print(f"Path not found: {full_path}")


def generate_output_filename(project_dir):
    """Generate output filename with timestamp."""
    project_name = Path(project_dir).name
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    return f"{project_name}_{timestamp}.md"


def main():
    args = parse_arguments()

    # Convert to Path and resolve
    project_dir = Path(args.project_dir).resolve()

    # Check if project directory exists
    if not project_dir.exists() or not project_dir.is_dir():
        print(f"Error: Project directory '{project_dir}' not found or is not a directory.")
        exit(1)

    # Expected files in project directory
    config_file = project_dir / 'config.ini'
    file_list_file = project_dir / 'files.txt'

    # Check if required files exist
    if not config_file.exists():
        print(f"Error: Configuration file '{config_file}' not found.")
        print("Expected config.ini with [Settings] section.")
        exit(1)

    if not file_list_file.exists():
        print(f"Error: File list '{file_list_file}' not found.")
        print("Expected files.txt containing list of files and directories to include.")
        exit(1)

    try:
        # Read configuration
        config = read_ini_config(config_file)

        # Get default language (from command line or config)
        if args.language:
            default_language = args.language
        elif 'default_language' in config:
            default_language = config['default_language']
        else:
            default_language = 'text'  # fallback

        # Read language mappings
        language_mappings = read_language_mappings(config_file)

        # Read filtering configuration
        filtering_config = read_filtering_config(config_file)

        # Get project root path
        if 'project_root' in config:
            project_root = Path(config['project_root']).resolve()
        else:
            print("Error: 'project_root' not specified in config.ini")
            exit(1)

        # Check if project root exists
        if not project_root.exists():
            print(f"Error: Project root directory '{project_root}' not found.")
            exit(1)

        # Read file list
        files_and_dirs = read_file_list(file_list_file)

        if not files_and_dirs:
            print("Warning: File list is empty.")

        # Generate output filename
        output_filename = generate_output_filename(project_dir)
        output_path = project_dir / output_filename

        # Generate markdown
        print(f"Generating project log...")
        print(f"Project directory: {project_dir}")
        print(f"Project root: {project_root}")
        print(f"Default language: {default_language}")
        print(f"Exclude files: {filtering_config['exclude_files']}")
        print(f"Clean comments: {filtering_config['clean_comments']}")
        print(f"Output file: {output_path}")
        print(f"Files to process: {len(files_and_dirs)}")
        print()

        with open(output_path, 'w', encoding='utf-8') as markdown_file:
            # Write header
            markdown_file.write(f"# Project: {project_dir.name}\n\n")
            markdown_file.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            # markdown_file.write(f"Default language: {default_language}\n")
            # markdown_file.write(f"Project root: {project_root}\n\n")
            # markdown_file.write("---\n\n")

            # Process each item from file list
            for item in files_and_dirs:
                process_path(item, markdown_file, project_root, default_language, language_mappings, filtering_config)

        print(f"\nProject log successfully generated: {output_path}")

    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()

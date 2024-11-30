import os
import yaml
import csv
from pathlib import Path
from typing import List, Dict, Any
from delepwn.utils.text_color import print_color

def ensure_dir(directory: str) -> None:
    """Ensure directory exists, create if it doesn't"""
    Path(directory).mkdir(parents=True, exist_ok=True)

def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file"""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print_color(f"Configuration file not found: {config_path}", color="red")
        raise
    except yaml.YAMLError as e:
        print_color(f"Error parsing YAML configuration: {e}", color="red")
        raise

def write_to_csv(filename: str, data: List[Any], headers: List[str] = None, mode: str = 'a') -> None:
    """Write data to CSV file"""
    try:
        with open(filename, mode=mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if headers and mode == 'w':
                writer.writerow(headers)
            writer.writerow(data)
    except Exception as e:
        print_color(f"Error writing to CSV file: {e}", color="red")
        raise

def get_unique_filename(base_path: str) -> str:
    """Get unique filename by appending number if file exists"""
    if not os.path.exists(base_path):
        return base_path
        
    base, ext = os.path.splitext(base_path)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    return f"{base}_{counter}{ext}"

def read_file_lines(filepath: str) -> List[str]:
    """Read file lines into list, stripping whitespace"""
    try:
        with open(filepath, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print_color(f"Error reading file {filepath}: {e}", color="red")
        raise
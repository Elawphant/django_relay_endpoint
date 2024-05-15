
from pathlib import Path
from typing import Dict
import re


def create_directory(dir_path: str):
    Path(dir_path).mkdir(parents=True, exist_ok=True)  # Using pathlib

def create_module(filename: str, folder_path: Path, content: str, overwrite=False):
    file_path = Path(folder_path / f"{filename}.py")
    if not file_path.exists() or overwrite == True:
        with open(file_path, 'w') as file:
            file.write(content)


def pascal_case(str: str):
    return ''.join(
            x for x in str.title() if not x.isspace())

def snake_case(str:str):
    snake_case = re.sub(r'[^a-zA-Z0-9_]+', '_', str)
    # Convert to lowercase
    snake_case = snake_case.lower()
    # Remove leading and trailing underscores
    snake_case = snake_case.strip('_')
    return snake_case


def name_class(typename: str, prefix: str = "", suffix:str = ""):
    return f"{prefix}{typename}{suffix}"
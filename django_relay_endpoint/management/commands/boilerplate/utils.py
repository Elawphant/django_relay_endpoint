
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


def pascal_case(text: str):
    text = re.sub(r"(_|-)+", " ", str(text))
    # Split text into words
    words = re.findall(r"[a-zA-Z0-9]+", str(text))
    # Capitalize each word
    words = [word.capitalize() for word in words]
    # Concatenate words
    return str("".join(words))

def snake_case(text):
    # Handle camelCase, kebab-case, and PascalCase
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(text))
    text = re.sub(r"[-\s]", "_", str(text))
    # Convert to lowercase and remove consecutive underscores
    return re.sub(r"_{2,}", "_", str(text)).lower()


def name_class(typename: str, prefix: str = "", suffix:str = ""):
    return f"{pascal_case(prefix)}{pascal_case(typename)}{pascal_case(suffix)}"


def name_module(typename: str, prefix: str = "", suffix:str = ""):
    return snake_case(f"{str(prefix) + '_' if prefix else ''}{str(typename)}_{str(suffix)}")

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
    text = re.sub(r"(_|-)+", " ", snake_case(str(text)))
    words = str(text).split(" ")
    # Concatenate words
    return "".join([word.title() for word in words])

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


schema = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "schema_app": {
      "type": "string",
      "description": "The app to place the generated files in"
    },
    "overwrite": {
      "type": "boolean",
      "description": "Overwrite existing files"
    },
    "type_config": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "model": {
            "type": "string",
            "description": "The model to generate the schema for"
          },
          "overwrite": {
            "type": "boolean",
            "description": "Overwrite existing files"
          },
          "query": {
            "type": "boolean",
            "description": "Generate the query module"
          },
          "query_fields": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "The queryable fields to include"
          },
          "create_mutation": {
            "type": "boolean",
            "description": "Generate the create mutation module"
          },
          "create_mutation_fields": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "The mutation fields to include"
          },
          "update_mutation": {
            "type": "boolean",
            "description": "Generate the update mutation module"
          },
          "update_mutation_fields": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "The mutation fields to include"
          },
          "delete_mutation": {
            "type": "boolean",
            "description": "Generate the delete mutation module"
          }
        },
        "required": ["model"]
      },
      "description": "Configuration for each type"
    }
  },
  "required": ["schema_app", "type_config"]
}

defaults = {
    "overwrite": False,
    "query": True,
    "create_mutation": True,
    "update_mutation": True,
    "delete_mutation": True,
    "query_fields": ["__all__"],
    "create_mutation_fields": ["__all__"],
    "update_mutation_fields": ["__all__"],
}


SUCCESS_MESSAGE = "The endpoint modules have been successfully configured in '{schema_app}'"
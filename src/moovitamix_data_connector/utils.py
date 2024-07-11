import os
from typing import List, Type

import yaml
from pydantic import BaseModel, ValidationError


def validate_datasource(json_records: List[dict], cls: Type) -> List[BaseModel]:
    validated_records = []
    for json_record in json_records:
        try:
            record = cls(**json_record)
            validated_records.append(record)
        except ValidationError as e:
            print(f"Pydantic {cls.__name__} Validation error: {e}")
    return validated_records

def load_yaml(file_path: str) -> dict:
    """
    Load a YAML file and return its content as a dictionary

    Args:
        file_path (str): Path to the YAML file

    Returns:
        dict: Content of the YAML file as a dictionary
    """
    try:
        with open(file_path) as file:
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")

def get_project_root() -> str:
    """
    Find the root path of the current project by searching for the 'conf' folder.

    Returns:
        str: The absolute path to the project root containing the 'conf' folder
    """
    current_path = os.getcwd()

    while current_path != os.path.dirname(current_path):
        if 'conf' in os.listdir(current_path):
            return current_path
        current_path = os.path.dirname(current_path)

    return None

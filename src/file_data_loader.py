from pathlib import Path
import csv
import json
import os
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FileDataLoader")

class FileDataLoader:
    def __init__(self, input_directory: str):
        self.input_directory = input_directory
        self.validate_directory()

    def validate_directory(self):
        """Validate the input directory."""
        if not os.path.isdir(self.input_directory):
            raise ValueError(f"The directory '{self.input_directory}' does not exist.")

    def get_files_by_extension(self) -> Dict[str, str]:
        """Get all files and their extensions in the directory."""
        path = Path(self.input_directory)
        logger.info(f"Scanning directory: {self.input_directory}")
        return {str(file.absolute()): file.suffix for file in path.rglob("*") if file.is_file()}

    def read_file(self, file_path: str) -> str:
        """Read the content of a file."""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    def parse_json_file(self, file_path: str) -> List[Any]:
        """Parse a JSON file."""
        return json.loads(self.read_file(file_path))

    def parse_csv_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse a CSV file into a list of dictionaries."""
        with open(file_path, 'r', encoding='ISO-8859-1') as csv_file:
            reader = csv.DictReader(csv_file)
            return [row for row in reader]

    def process_directory(self) -> List[Dict[str, Any]]:
        """Process all files in the directory."""
        file_info = self.get_files_by_extension()
        entries = []

        FILE_PROCESSORS = {
            '.csv': self.parse_csv_file,
            '.json': self.parse_json_file,
            '.txt': self.read_file,
        }

        for file_path, extension in file_info.items():
            processor = FILE_PROCESSORS.get(extension)
            if processor:
                result = processor(file_path)
                if isinstance(result, list):
                    entries.extend(result)
                else:
                    entries.append({"text": result})
            else:
                logger.warning(f"Unsupported file type: {extension}")
        print(f"Parsed {len(entries)} entries.")
        return entries
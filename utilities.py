import logging
import hashlib
import json
from pathlib import Path
import csv
import os

def is_binary(file_path):
    """
    Check if a file is binary.
    """
    try:
        with open(file_path, 'rb') as file:
            CHUNKSIZE = 1024
            while True:
                chunk = file.read(CHUNKSIZE)
                if b'\0' in chunk:  # Check for null byte
                    return True
                if len(chunk) < CHUNKSIZE:
                    break
    except (OSError, IOError) as e:
        logging.exception(f"Error reading file {file_path}: {e}")
    return False

def save_to_jsonl(file_data, output_file):
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'a') as f:
            json.dump(file_data, f, default=lambda o: repr(o))
            f.write('\n')
        logging.info(f"Successfully saved data to {output_file}")
    except (OSError, IOError, ValueError) as e:
        logging.exception(f"Error saving data to {output_file}: {e}")

def cache_analysis_results(codebase_data):
    cache = {}
    for _, module_data in codebase_data.items():
        for file_data in module_data:
            try:
                if file_data['content'] is not None:
                    file_hash = hashlib.md5(file_data['content'].encode('utf-8')).hexdigest()
                else:
                    file_hash = None
                cache[file_data['file_path']] = {
                    'hash': file_hash,
                    'analysis': file_data['analysis'],
                    'function_count': calculate_function_count(file_data),
                    'comment_density': calculate_comment_density(file_data)
                }
            except KeyError as e:
                logging.exception(f"Missing key in file data: {e}")
            except Exception as e:
                logging.exception(f"Unexpected error caching analysis results: {e}")
    try:
        with open('analysis_cache.json', 'w') as f:
            json.dump(cache, f, default=lambda o: repr(o))
        logging.info("Successfully cached analysis results")
    except (OSError, IOError, ValueError) as e:
        logging.exception(f"Error caching analysis results: {e}")

def load_analysis_cache():
    try:
        if Path('analysis_cache.json').exists():
            with open('analysis_cache.json', 'r') as f:
                return json.load(f)
    except (OSError, IOError, ValueError) as e:
        logging.exception(f"Error loading analysis cache: {e}")
    return {}

def load_documentation_links(csv_file):
    links = {}
    try:
        if Path(csv_file).exists():
            with open(csv_file, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    links[row['File']] = row['Documentation']
    except (OSError, IOError, ValueError, KeyError) as e:
        logging.exception(f"Error loading documentation links: {e}")
    return links

def verify_jsonl(output_file):
    logging.info(f"Checking if JSONL file exists at {output_file}")
    try:
        Path(output_file).touch(exist_ok=True)  # Ensure the file exists
        with open(output_file, 'r') as file:
            for line in file:
                json.loads(line)
        logging.info("JSONL file is valid and exists.")
        return True
    except json.JSONDecodeError as e:
        logging.exception(f"JSONL file validation failed due to JSON decode error: {e}")
    except (FileNotFoundError, OSError, IOError) as e:
        logging.exception(f"Error accessing JSONL file at {output_file}: {e}")
    return False

def calculate_function_count(file_data):
    try:
        if file_data['language'] == 'Python':
            return len(file_data['analysis']['functions'])
        elif file_data['language'] == 'JavaScript':
            return len(file_data['analysis']['functions'])
        else:
            return 0
    except KeyError as e:
        logging.exception(f"Missing key in file data: {e}")
    except Exception as e:
        logging.exception(f"Unexpected error calculating function count: {e}")
    return 0

def calculate_comment_density(file_data):
    try:
        loc = file_data['metadata']['loc']
        comment_count = len(file_data['analysis'].get('comments', []))
        if loc > 0:
            return comment_count / loc
        else:
            return 0
    except KeyError as e:
        logging.exception(f"Missing key in file data: {e}")
    except Exception as e:
        logging.exception(f"Unexpected error calculating comment density: {e}")
    return 0
import jsonschema
import logging

schema = {
    "type": "object",
    "properties": {
        "file_path": {"type": "string"},
        "language": {"type": "string"},
        "content": {"type": ["string", "null"]},
        "analysis": {
            "type": "object",
            "properties": {
                "classes": {"type": "array"},
                "functions": {"type": "array"},
                "imports": {"type": "array"},
                "lint_results": {"type": "object"},
                "docstrings": {"type": "object"},
                "comments": {"type": "array"},
                "html": {"type": "string"},
                "tags": {"type": "array"},
                "attributes": {"type": "object"},
                "entities": {"type": "array"},
                "complexity": {"type": "number"},
                "data": {"type": "object"},
                "jsx_analysis": {"type": "object"},
                "vue_analysis": {"type": "object"}
            },
            "additionalProperties": True
        },
        "metadata": {
            "type": "object",
            "properties": {
                "loc": {"type": "integer"},
                "size": {"type": "integer"},
                "md5_hash": {"type": "string"}
            },
            "required": ["size"],
            "additionalProperties": True
        }
    },
    "required": ["file_path", "language", "content", "analysis", "metadata"]
}

def validate_json(data):
    try:
        jsonschema.validate(instance=data, schema=schema)
        logging.info(f"JSON data validation successful for {data['file_path']}")
        return True
    except jsonschema.exceptions.ValidationError as e:
        logging.error(f"Validation error in {data['file_path']}: {e.message}, in {e.path}")
        return False
    except KeyError as e:
        logging.error(f"Missing key in JSON data: {e}")
        return False

def validate_file_path(file_path):
    if not file_path:
        logging.error("File path is empty or None")
        return False
    return True

def validate_language(language):
    supported_languages = [
        "python", "javascript", "html", "css", "json", "markdown", "text", "yaml", "xml",
        "image", "document", "unknown", "typescript", "jsx", "vue"
    ]
    if language not in supported_languages:
        logging.warning(f"Unsupported language: {language}")
        return False
    return True

def validate_content(content):
    if content is None:
        logging.info("File content is None (binary or unreadable file)")
        return True
    if not content:
        logging.warning("File content is empty")
        return False
    return True

def validate_analysis(analysis):
    if not analysis:
        logging.warning("Analysis data is empty")
        return True
    return True

def validate_metadata(metadata):
    if not metadata:
        logging.warning("Metadata is empty")
        return False
    if "size" not in metadata:
        logging.error("File size is missing in metadata")
        return False
    if metadata["size"] < 0:
        logging.error("Invalid file size in metadata")
        return False
    return True

def validate_data(data):
    if not validate_file_path(data.get("file_path")):
        return False
    if not validate_language(data.get("language")):
        return False
    if not validate_content(data.get("content")):
        return False
    if not validate_analysis(data.get("analysis")):
        return False
    if not validate_metadata(data.get("metadata")):
        return False
    if not validate_json(data):
        return False
    logging.info(f"Data validation successful for {data['file_path']}")
    return True
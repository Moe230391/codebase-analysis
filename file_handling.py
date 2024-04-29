import filetype
import magic
import logging
import aiofiles
import pygments
from pygments.lexers import get_lexer_for_filename, guess_lexer

TEXT_FILE_EXTENSIONS = [
    '.txt', '.md', '.html', '.htm', '.json', '.css', '.xml', '.yml', '.yaml', '.csv', '.ini', '.cfg',
    '.conf', '.py', '.js', '.ts', '.jsx', '.tsx', '.php', '.sh', '.bat', '.ps1', '.sql', '.log',
    '.gitignore', '.npmignore', '.jshintrc', '.eslintrc', '.babelrc', '.editorconfig', '.markdown',
    '.mdx', '.rst', '.asciidoc', '.vue', '.scss', '.sass', '.node', '.mts', '.coffee', '.applescript',
    '.c', '.jinja2', '.h', '.py-tpl', '.cpp', '.hpp', '.asm', '.pyx', '.f', '.template', '.keep', '.R',
    '.go', '.rs', '.pyw', '.misc', '.message', '.no_trailing_newline', '.g', '.csh', '.asp', '.htm', '.in'
]

async def guess_file_type(file_path):
    try:
        kind = filetype.guess(file_path)
        if kind is None or not kind.mime:
            mime_type = magic.from_file(file_path, mime=True)
            if not mime_type:
                logging.warning(f"Unable to determine the file type for: {file_path}")
                return None
            logging.info(f"Determined file type using magic: {mime_type} for file: {file_path}")
            return mime_type
        else:
            logging.info(f"Determined file type using filetype: {kind.mime} for file: {file_path}")
            return kind.mime
    except (IOError, PermissionError) as e:
        logging.error(f"Error guessing file type for: {file_path}, Error: {e}")
        return None

async def guess_language(file_path):
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            content = await file.read()
        try:
            lexer = get_lexer_for_filename(file_path)
        except pygments.util.ClassNotFound:
            lexer = guess_lexer(content)
        language = lexer.name
        logging.info(f"Detected language: {language} for file: {file_path}")
        return language.lower()
    except (IOError, PermissionError) as e:
        logging.error(f"Error opening or reading file for language guessing: {file_path}, Error: {e}")
        return None
    except Exception as e:
        logging.exception(f"Unexpected error occurred while guessing language for file: {file_path}, Error: {str(e)}")
        return None
        
async def is_text_file(file_path):
    try:
        file_type = await guess_file_type(file_path)
        text_types = ['text/plain', 'text/html', 'text/css', 'text/javascript', 'application/json', 'application/xml']
        if file_type in text_types:
            return True
        return False
    except Exception as e:
        logging.error(f"Failed to determine if file is text for {file_path}: {str(e)}")
        return False
  
    
async def is_binary_file(file_path):
    try:
        return not await is_text_file(file_path)
    except Exception as e:
        logging.error(f"Failed to determine if file is binary for {file_path}: {str(e)}")
        return True  # Assume binary if there's an error determining file type


async def read_text_file(file_path):
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            content = await file.read()
        logging.info(f"Successfully read text file: {file_path}")
        return content
    except (IOError, PermissionError, UnicodeDecodeError) as e:
        logging.warning(f"Skipping unreadable or improperly encoded file: {file_path}, Error: {e}")
        return None

async def async_read(file_path):
    if await is_binary_file(file_path):
        logging.info(f"Skipping binary file: {file_path}")
        return None
    return await read_text_file(file_path)
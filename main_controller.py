import asyncio
import concurrent.futures
import multiprocessing
import os
import time
import logging
import spacy
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt
from file_handling import guess_file_type, guess_language, is_binary_file
from analysis import (
    count_skipped_files,
    process_document_file,
    process_image_file,
    process_json_file,
    process_jsx_file,
    process_markdown_file,
    process_python_file,
    process_html_file,
    process_css_file,
    process_javascript_file,
    default_handler,
    analyze_lint_results,
    process_text_file,
    process_typescript_file,
    process_vue_file,
    process_xml_file,
    process_yaml_file
)
from utilities import (
    save_to_jsonl,
    cache_analysis_results,
    load_analysis_cache,
    load_documentation_links,
    calculate_function_count, 
    calculate_comment_density,
)
from graph_management import (
    build_dependency_graph,
    visualize_dependency_graph,
    build_call_graph,
    visualize_call_graph
)
import hashlib

FILE_TYPE_HANDLERS = {
    '.py': process_python_file,
    '.js': process_javascript_file,
    '.html': process_html_file,
    '.css': process_css_file,
    '.json': process_json_file,
    '.md': process_markdown_file,
    '.txt': process_text_file,
    '.pyi': process_python_file,
    '.ts': process_typescript_file,
    '.tsx': process_typescript_file,
    '.jsx': process_jsx_file,
    '.mjs': process_javascript_file,
    '.cjs': process_javascript_file,
    '.vue': process_vue_file,
    '.yaml': process_yaml_file,
    '.yml': process_yaml_file,
    '.xml': process_xml_file,
    '.png': process_image_file,
    '.jpg': process_image_file,
    '.jpeg': process_image_file,
    '.gif': process_image_file,
    '.bmp': process_image_file,
    '.ico': process_image_file,
    '.svg': process_image_file,
    '.doc': process_document_file,
    '.pdf': process_document_file,
    '.odt': process_document_file,
    '.docx': process_document_file,
    '.xlsx': process_document_file,
    '.ppt': process_document_file,
    '.pptx': process_document_file,
    '.vue': process_vue_file,
    '.scss': process_css_file,
    '.sass': process_css_file,
    '.node': process_javascript_file,
    '.mts': process_typescript_file,
    '.coffee': process_javascript_file,
    '.applescript': process_text_file,
    '.c': process_text_file,
    '.jinja2': process_text_file,
    '.h': process_text_file,
    '.py-tpl': process_python_file,
    '.cpp': process_text_file,
    '.hpp': process_text_file,
    '.asm': process_text_file,
    '.pyx': process_python_file,
    '.f': process_text_file,
    '.template': process_text_file,
    '.keep': process_text_file,
    '.R': process_text_file,
    '.go': process_text_file,
    '.rs': process_text_file,
    '.pyw': process_python_file,
    '.misc': process_text_file,
    '.message': process_text_file,
    '.no_trailing_newline': process_text_file,
    '.g': process_text_file,
    '.csh': process_text_file,
    '.asp': process_text_file,
    '.htm': process_html_file,
    '.in': process_text_file
}

nlp = spacy.load('en_core_web_lg')

async def main():
    root_dir = '#Add root directory here (make sure directory is cleaned of Binary filetypes)'
    output_dir = '#Provide your output directory'
    os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists
    doc_links_csv = '#Any csv file containing docs link'
    graph_dir = '#Add directory for adding graphs'
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("codebase_mirror.log"),
            logging.StreamHandler()
        ]
    )

    try:
        start_time = time.time()
        codebase_data = process_all_directories(root_dir, output_dir, nlp)
        end_time = time.time()
        logging.info(f"Codebase analysis completed in {end_time - start_time:.2f} seconds")
    except Exception as e:
        logging.exception(f"Error processing codebase: {str(e)}")
        return
    
    try:
        skipped_files = count_skipped_files(codebase_data)
        logging.info(f"Skipped Files: {skipped_files}")
    except Exception as e:
        logging.exception(f"Error counting skipped files: {str(e)}")
    
    try:
        analysis_cache = load_analysis_cache()
        doc_links = load_documentation_links(doc_links_csv)
    except Exception as e:
        logging.exception(f"Error loading analysis cache or documentation links: {str(e)}")
    
    for module_path, module_data in codebase_data.items():
        for file_data in module_data:
            try:
                file_hash = hashlib.md5(file_data['content'].encode('utf-8')).hexdigest()
                if file_data['file_path'] in analysis_cache and analysis_cache[file_data['file_path']]['hash'] == file_hash:
                    file_data['analysis'] = analysis_cache[file_data['file_path']]['analysis']
                if file_data['file_path'] in doc_links:
                    file_data['documentation'] = doc_links[file_data['file_path']]
                    file_data['module_path'] = module_path
            except KeyError as e:
                logging.exception(f"Error updating file data: {str(e)}")
            except Exception as e:
                logging.exception(f"Unexpected error updating file data: {str(e)}")
    
    try:
        dependency_graph = build_dependency_graph(codebase_data)
        visualize_dependency_graph(dependency_graph, output_dir=graph_dir)
    except Exception as e:
        logging.exception(f"Error building or visualizing dependency graph: {str(e)}")
    
    try:
        call_graph = build_call_graph(codebase_data)
        visualize_call_graph(call_graph, output_dir=graph_dir)
    except Exception as e:
        logging.exception(f"Error building or visualizing call graph: {str(e)}")
    
    try:
        lint_stats = analyze_lint_results(codebase_data)
        logging.info("Lint Violation Statistics:")
        for violation, count in lint_stats.items():
            logging.info(f"{violation}: {count}")
    except Exception as e:
        logging.exception(f"Error analyzing lint results: {str(e)}")
    
    try:
        codebase_stats = calculate_codebase_stats(codebase_data)
        logging.info("Codebase Statistics:")
        logging.info(f"Total Files: {codebase_stats['total_files']}")
        logging.info(f"Total LOC: {codebase_stats['total_loc']}")
        logging.info(f"Total Size: {codebase_stats['total_size']} bytes")
        logging.info(f"Files by Language: {codebase_stats['files_by_language']}")
        logging.info(f"LOC by Language: {codebase_stats['loc_by_language']}")
        logging.info(f"Size by Language: {codebase_stats['size_by_language']}")
    except Exception as e:
        logging.exception(f"Error calculating codebase statistics: {str(e)}")
    
    try:
        cache_analysis_results(codebase_data)
    except Exception as e:
        logging.exception(f"Error caching analysis results: {str(e)}")


async def process_file(file_path, module_path, output_dir, nlp):
    logging.info(f"Starting processing of file: {file_path}")
    try:
        if not Path(file_path).exists():
            logging.error(f"File not found: {file_path}")
            return
        logging.info(f"Reading file: {file_path}")

        if await is_binary_file(file_path):
            logging.info(f"Skipping binary file: {file_path}")
            return

        file_type = await guess_file_type(file_path)
        language = await guess_language(file_path)
        logging.info(f"File type: {file_type}")
        logging.info(f"Language: {language}")

        handler = FILE_TYPE_HANDLERS.get(file_type, default_handler)
        if handler:
            logging.info(f"Using handler {handler.__name__} for file: {file_path}")
            file_data = await handler(file_path, module_path, language, nlp)
            if file_data:
                file_data['language'] = language
                doc = nlp(file_data['content'])
                entities = [{'text': ent.text, 'label': ent.label_} for ent in doc.ents]
                file_data['analysis']['entities'] = entities
                file_data['analysis']['function_count'] = calculate_function_count(file_data)
                file_data['analysis']['comment_density'] = calculate_comment_density(file_data)
                logging.info(f"Processed file: {file_path}")
                print(f"Processed file: {file_path}")
                print(f"Language: {file_data['language']}")
                print(f"Entities: {file_data['analysis']['entities']}")
                print(f"Function Count: {file_data['analysis']['function_count']}")
                print(f"Comment Density: {file_data['analysis']['comment_density']}")
                logging.info(f"File data processed for file: {file_path}")
                if not module_path:
                    logging.error(f"Invalid module path for file: {file_path}")
                    return
                module_jsonl_file = f"{output_dir}/{module_path}.jsonl"
                logging.info(f"Saving processed data to {module_jsonl_file}")
                save_to_jsonl(file_data, module_jsonl_file)
                logging.info(f"Processed data saved to {module_jsonl_file}")
            else:
                logging.error(f"Data validation failed for file: {file_path}")
        else:
            logging.error(f"No handler found for file type: {file_type} at {file_path}")
    except UnicodeDecodeError as e:
        logging.exception(f"Unicode decode error in file {file_path}: {str(e)}")
    except Exception as e:
        logging.exception(f"Unhandled error processing file: {file_path}, Error: {str(e)}")
    finally:
        logging.info(f"Finished processing file: {file_path}")
        
def process_file_in_pool(args):
    try:
        file_path, module_path, output_dir, nlp = args
        asyncio.run(process_file(file_path, module_path, output_dir, nlp))
    except Exception as e:
        logging.exception(f"Error processing file in pool: {str(e)}")

def process_directory_concurrently(directory_path, root_dir, output_dir, nlp):
    codebase_data = {}
    try:
        file_paths = [p for p in Path(directory_path).rglob('*') if p.is_file()]
        max_workers = multiprocessing.cpu_count()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            args_list = [(str(file_path), os.path.relpath(file_path.parent, root_dir), output_dir, nlp) for file_path in file_paths]
            executor.map(process_file_in_pool, args_list)
    except Exception as e:
        logging.exception(f"Error processing directory concurrently: {str(e)}")
    return codebase_data

def process_all_directories(root_dir, output_dir, nlp):
    codebase_data = {}
    try:
        for root, _, _ in os.walk(root_dir):
            logging.info(f"Processing directory: {root}")
            directory_data = process_directory_concurrently(root, root_dir, output_dir, nlp)
            codebase_data.update(directory_data)
    except Exception as e:
        logging.exception(f"Error processing all directories: {str(e)}")
    return codebase_data

def calculate_codebase_stats(codebase_data):
    stats = {
        'total_files': 0,
        'total_loc': 0,
        'total_size': 0,
        'files_by_language': {},
        'loc_by_language': {},
        'size_by_language': {},
        'files_by_module': {}
    }
    for module_path, module_data in codebase_data.items():
        stats['files_by_module'][module_path] = len(module_data)
        for file_data in module_data:
            try:
                stats['total_files'] += 1
                stats['total_loc'] += file_data['metadata']['loc']
                stats['total_size'] += file_data['metadata']['size']
                language = file_data['language']
                if language not in stats['files_by_language']:
                    stats['files_by_language'][language] = 0
                    stats['loc_by_language'][language] = 0
                    stats['size_by_language'][language] = 0
                stats['files_by_language'][language] += 1
                stats['loc_by_language'][language] += file_data['metadata']['loc']
                stats['size_by_language'][language] += file_data['metadata']['size']
            except KeyError as e:
                logging.exception(f"Error calculating codebase stats: {str(e)}")
            except Exception as e:
                logging.exception(f"Unexpected error calculating codebase stats: {str(e)}")
    return stats


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    asyncio.run(main())
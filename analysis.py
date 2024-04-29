import ast
import re
import subprocess
import logging
import os
import json
from file_handling import async_read
from data_validation import validate_json
from utilities import save_to_jsonl
import networkx as nx
import markdown
import yaml
from radon.complexity import cc_visit
import esprima
from bs4 import BeautifulSoup
import cssutils

def extract_docstrings_and_comments(file_content):
    parsed_content = ast.parse(file_content)
    docstrings = {}
    comments = []

    for node in ast.walk(parsed_content):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            docstring = ast.get_docstring(node)
            if docstring:
                docstrings[node.name if hasattr(node, 'name') else 'module'] = docstring

    for line in file_content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            comments.append(line)

    return docstrings, comments

def analyze_function_calls(function_node):
    call_graph = nx.DiGraph()
    for node in ast.walk(function_node):
        if isinstance(node, ast.Call):
            callee = resolve_function_name(node.func)
            call_graph.add_edge(function_node.name, callee)
    return call_graph

def resolve_function_name(func_node):
    if isinstance(func_node, ast.Name):
        return func_node.id
    elif isinstance(func_node, ast.Attribute):
        return func_node.attr
    return "unknown_function"

async def process_python_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading Python file: {file_path}")
        content = await async_read(file_path)
        logging.info(f"Parsing Python file: {file_path}")
        tree = ast.parse(content)
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.Import)]
        imports.extend([node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)])
        docstrings, comments = extract_docstrings_and_comments(content)
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        complexity = cc_visit(content)
        logging.info(f"Running linter on Python file: {file_path}")
        lint_results = subprocess.run(['pylint', '--output-format=json', file_path], capture_output=True, text=True)
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'classes': [{'name': cls.name, 'methods': [{'name': func.name, 'params': [arg.arg for arg in func.args.args], 'call_graph': analyze_function_calls(func)} for func in cls.body if isinstance(func, ast.FunctionDef)]} for cls in classes],
                'functions': [{'name': func.name, 'params': [arg.arg for arg in func.args.args], 'call_graph': analyze_function_calls(func)} for func in functions if not any(func in cls.body for cls in classes)],
                'imports': imports,
                'docstrings': docstrings,
                'comments': comments,
                'entities': entities,
                'complexity': complexity.total_complexity,
                'lint_results': json.loads(lint_results.stdout) if lint_results.returncode == 0 else None
            },
            'metadata': {
                'loc': len(content.split('\n')),
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        logging.info(f"Validating processed data for Python file: {file_path}")
        if validate_json(data):
            logging.info(f"Saving processed data to {module_path}.jsonl")
            save_to_jsonl(data, f"{module_path}.jsonl")
            logging.info(f"Processed data saved to {module_path}.jsonl")
            return data
        else:
            logging.error(f"Data validation failed for Python file: {file_path}")
            return None
    except Exception as e:
        logging.error(f"Error processing Python file: {file_path}, Error: {str(e)}")
        return None

async def process_html_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading HTML file: {file_path}")
        content = await async_read(file_path)
        logging.info(f"Parsing HTML file: {file_path}")
        soup = BeautifulSoup(content, 'html.parser')
        tags = [tag.name for tag in soup.find_all()]
        attributes = {tag.name: tag.attrs for tag in soup.find_all()}
        docstrings = {}
        comments = [comment.extract() for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.startswith('<!--'))]
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'tags': tags,
                'attributes': attributes,
                'docstrings': docstrings,
                'comments': comments,
                'entities': entities
            },
            'metadata': {
                'loc': len(content.split('\n')),
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        logging.info(f"Validating processed data for HTML file: {file_path}")
        if validate_json(data):
            logging.info(f"Saving processed data to {module_path}.jsonl")
            save_to_jsonl(data, f"{module_path}.jsonl")
            logging.info(f"Processed data saved to {module_path}.jsonl")
            return data
        else:
            logging.error(f"Data validation failed for HTML file: {file_path}")
            return None
    except Exception as e:
        logging.error(f"Error processing HTML file: {file_path}, Error: {str(e)}")
        return None

async def process_css_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading CSS file: {file_path}")
        content = await async_read(file_path)
        logging.info(f"Parsing CSS file: {file_path}")
        sheet = cssutils.parseString(content)
        rules = [rule.selectorText for rule in sheet]
        properties = {rule.selectorText: [prop.name for prop in rule.style] for rule in sheet}
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        logging.info(f"Running linter on CSS file: {file_path}")
        lint_results = subprocess.run(['stylelint', '--formatter=json', file_path], capture_output=True, text=True)
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'rules': rules,
                'properties': properties,
                'entities': entities,
                'lint_results': json.loads(lint_results.stdout) if lint_results.returncode == 0 else None
            },
            'metadata': {
                'loc': len(content.split('\n')),
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        logging.info(f"Validating processed data for CSS file: {file_path}")
        if validate_json(data):
            logging.info(f"Saving processed data to {module_path}.jsonl")
            save_to_jsonl(data, f"{module_path}.jsonl")
            logging.info(f"Processed data saved to {module_path}.jsonl")
            return data
        else:
            logging.error(f"Data validation failed for CSS file: {file_path}")
            return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed for CSS file: {file_path}, Error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error processing CSS file: {file_path}, Error: {str(e)}")
        return None

async def process_javascript_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading JavaScript file: {file_path}")
        content = await async_read(file_path)
        logging.info(f"Parsing JavaScript file: {file_path}")
        tree = esprima.parseScript(content, {'comment': True})
        functions = [node for node in esprima.walk(tree) if node.type == 'FunctionDeclaration']
        imports = [node.source.value for node in esprima.walk(tree) if node.type == 'ImportDeclaration']
        comments = [comment.value.strip() for comment in tree.comments]
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        logging.info(f"Running linter on JavaScript file: {file_path}")
        lint_results = subprocess.run(['eslint', '--format=json', file_path], capture_output=True, text=True)
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'functions': [{'name': func.id.name, 'params': [p.name for p in func.params]} for func in functions],
                'imports': imports,
                'comments': comments,
                'entities': entities,
                'lint_results': json.loads(lint_results.stdout) if lint_results.returncode == 0 else None
            },
            'metadata': {
                'loc': len(content.split('\n')),
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        logging.info(f"Validating processed data for JavaScript file: {file_path}")
        if validate_json(data):
            logging.info(f"Saving processed data to {module_path}.jsonl")
            save_to_jsonl(data, f"{module_path}.jsonl")
            logging.info(f"Processed data saved to {module_path}.jsonl")
            return data
        else:
            logging.error(f"Data validation failed for JavaScript file: {file_path}")
            return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed for JavaScript file: {file_path}, Error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error processing JavaScript file: {file_path}, Error: {str(e)}")
        return None

async def process_json_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading JSON file: {file_path}")
        content = await async_read(file_path)
        data_json = json.loads(content)
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'data': data_json,
                'entities': entities
            },
            'metadata': {
                'loc': len(content.split('\n')),
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        return data
    except Exception as e:
        logging.error(f"Error processing JSON file: {file_path}, Error: {str(e)}")
        return None

async def process_markdown_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading Markdown file: {file_path}")
        content = await async_read(file_path)
        html = markdown.markdown(content)
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'html': html,
                'entities': entities
            },
            'metadata': {
                'loc': len(content.split('\n')),
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        return data
    except Exception as e:
        logging.error(f"Error processing Markdown file: {file_path}, Error: {str(e)}")
        return None

async def process_text_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading Text file: {file_path}")
        content = await async_read(file_path)
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'entities': entities
            },
            'metadata': {
                'loc': len(content.split('\n')),
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        return data
    except Exception as e:
        logging.error(f"Error processing Text file: {file_path}, Error: {str(e)}")
        return None

async def process_yaml_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading YAML file: {file_path}")
        content = await async_read(file_path)
        data_yaml = yaml.safe_load(content)
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'data': data_yaml,
                'entities': entities
            },
            'metadata': {
                'loc': len(content.split('\n')),
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        return data
    except Exception as e:
        logging.error(f"Error processing YAML file: {file_path}, Error: {str(e)}")
        return None

async def process_xml_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading XML file: {file_path}")
        content = await async_read(file_path)
        soup = BeautifulSoup(content, 'lxml')
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'tags': [tag.name for tag in soup.find_all()],
                'attributes': {tag.name: tag.attrs for tag in soup.find_all()},
                'entities': entities
            },
            'metadata': {
                'loc': len(content.split('\n')),
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        return data
    except Exception as e:
        logging.error(f"Error processing XML file: {file_path}, Error: {str(e)}")
        return None

async def process_image_file(file_path, module_path):
    try:
        logging.info(f"Reading Image file: {file_path}")
        data = {
            'file_path': file_path,
            'language': 'image',
            'content': None,
            'analysis': {},
            'metadata': {
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        return data
    except Exception as e:
        logging.error(f"Error processing Image file: {file_path}, Error: {str(e)}")
        return None

async def process_document_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading Document file: {file_path}")
        content = await async_read(file_path)
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents] if content else []
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'entities': entities
            },
            'metadata': {
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        return data
    except Exception as e:
        logging.error(f"Error processing Document file: {file_path}, Error: {str(e)}")
    return None

async def process_typescript_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading TypeScript file: {file_path}")
        content = await async_read(file_path)
        if content is None:
            logging.warning(f"Skipping binary or empty TypeScript file: {file_path}")
            return None
        tree = esprima.parseScript(content, {'comment': True})
        functions = [node for node in esprima.walk(tree) if node.type == 'FunctionDeclaration']
        imports = [node.source.value for node in esprima.walk(tree) if node.type == 'ImportDeclaration']
        comments = [comment.value.strip() for comment in tree.comments]
        complexity = cc_visit(content)
        docstrings = {}
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        logging.info(f"Running linter on TypeScript file: {file_path}")
        lint_results = subprocess.run(['tslint', '--format=json', file_path], capture_output=True, text=True)
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'functions': [{'name': func.id.name, 'params': [p.name for p in func.params]} for func in functions],
                'imports': imports,
                'comments': comments,
                'complexity': complexity.total_complexity,
                'docstrings': docstrings,
                'entities': entities,
                'lint_results': json.loads(lint_results.stdout) if lint_results.returncode == 0 else None
            },
            'metadata': {
                'loc': len(content.split('\n')),
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        logging.info(f"Validating processed data for TypeScript file: {file_path}")
        if validate_json(data):
            logging.info(f"Saving processed data to {module_path}.jsonl")
            save_to_jsonl(data, f"{module_path}.jsonl")
            logging.info(f"Processed data saved to {module_path}.jsonl")
            return data
        else:
            logging.error(f"Data validation failed for TypeScript file: {file_path}")
            return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed for TypeScript file: {file_path}, Error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error processing TypeScript file: {file_path}, Error: {str(e)}")
        return None

async def process_jsx_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading JSX file: {file_path}")
        content = await async_read(file_path)
        if content is None:
            logging.warning(f"Skipping binary or empty JSX file: {file_path}")
            return None
        result = subprocess.run(['node', 'parse_jsx.js', file_path], capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Error parsing JSX file: {file_path}, {result.stderr}")
            return None
        analysis = json.loads(result.stdout)
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'entities': entities,
                'jsx_analysis': analysis
            },
            'metadata': {
                'loc': len(content.split('\n')),
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        logging.info(f"Validating processed data for JSX file: {file_path}")
        if validate_json(data):
            logging.info(f"Saving processed data to {module_path}.jsonl")
            save_to_jsonl(data, f"{module_path}.jsonl")
            logging.info(f"Processed data saved to {module_path}.jsonl")
            return data
        else:
            logging.error(f"Data validation failed for JSX file: {file_path}")
            return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed for JSX file: {file_path}, Error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error processing JSX file: {file_path}, Error: {str(e)}")
        return None

async def process_vue_file(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading Vue file: {file_path}")
        content = await async_read(file_path)
        if content is None:
            logging.warning(f"Skipping binary or empty Vue file: {file_path}")
            return None
        result = subprocess.run(['node', 'parse_vue.js', file_path], capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Error parsing Vue file: {file_path}, {result.stderr}")
            return None
        analysis = json.loads(result.stdout)
        entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'entities': entities,
                'vue_analysis': analysis
            },
            'metadata': {
                'loc': len(content.split('\n')),
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        logging.info(f"Validating processed data for Vue file: {file_path}")
        if validate_json(data):
            logging.info(f"Saving processed data to {module_path}.jsonl")
            save_to_jsonl(data, f"{module_path}.jsonl")
            logging.info(f"Processed data saved to {module_path}.jsonl")
            return data
        else:
            logging.error(f"Data validation failed for Vue file: {file_path}")
            return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed for Vue file: {file_path}, Error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error processing Vue file: {file_path}, Error: {str(e)}")
        return None

async def default_handler(file_path, module_path, language, nlp):
    try:
        logging.info(f"Reading file: {file_path}")
        content = await async_read(file_path)
        if content is None:
            logging.warning(f"Skipping file due to being binary or unsupported: {file_path}")
            entities = []
        else:
            entities = [{'text': ent.text, 'label': ent.label_} for ent in nlp(content).ents]
        data = {
            'file_path': file_path,
            'language': language,
            'content': content,
            'analysis': {
                'entities': entities
            },
            'metadata': {
                'loc': len(content.split('\n')) if content else 0,
                'size': os.path.getsize(file_path)
            },
            'module_path': module_path
        }
        return data
    except Exception as e:
        logging.error(f"Error processing file: {file_path}, Error: {str(e)}")
        return None

def analyze_lint_results(codebase_data):
    lint_stats = {}
    for module_data in codebase_data.values():
        for file_data in module_data:
            if file_data:
                if file_data['language'] == 'python':
                    lint_results = file_data['analysis'].get('lint_results')
                    if lint_results:
                        for item in lint_results:
                            violation_type = item['symbol']
                            lint_stats[violation_type] = lint_stats.get(violation_type, 0) + 1
                elif file_data['language'] == 'javascript':
                    lint_results = file_data['analysis'].get('lint_results')
                    if lint_results:
                        for item in lint_results:
                            if 'errorCount' in item:
                                violation_type = 'error'
                                lint_stats[violation_type] = lint_stats.get(violation_type, 0) + item['errorCount']
                            if 'warningCount' in item:
                                violation_type = 'warning'
                                lint_stats[violation_type] = lint_stats.get(violation_type, 0) + item['warningCount']
                elif file_data['language'] == 'css':
                    lint_results = file_data['analysis'].get('lint_results')
                    if lint_results:
                        for item in lint_results:
                            violation_type = item['rule']
                            lint_stats[violation_type] = lint_stats.get(violation_type, 0) + 1
                elif file_data['language'] == 'typescript':
                    lint_results = file_data['analysis'].get('lint_results')
                    if lint_results:
                        for item in lint_results:
                            violation_type = item['ruleName']
                            lint_stats[violation_type] = lint_stats.get(violation_type, 0) + 1
    return lint_stats

def count_skipped_files(codebase_data):
    skipped_files = 0
    for module_data in codebase_data.values():
        for file_data in module_data:
            if file_data is None:
                skipped_files += 1
    return skipped_files
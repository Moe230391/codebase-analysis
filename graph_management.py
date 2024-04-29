import networkx as nx
import matplotlib.pyplot as plt
import pyan
import logging
from pathlib import Path
import os

def resolve_import(import_statement, file_path, codebase_data):
    module_path = str(Path(file_path).parent)
    file_ext = Path(file_path).suffix  # Capture the file extension of the importing file

    # Generate possible file paths based on different extensions
    possible_extensions = ['.py', '.js', '.ts', '.jsx', '.vue', '.scss', '.css', '.sass', '.html', '.tsx', '.xml', '.php', '.c', '.cpp', '.hpp', '.go', '.rs'] + [file_ext]
    possible_paths = [import_statement.replace('.', '/') + ext for ext in possible_extensions]

    # Check within the same module
    for data in codebase_data.get(module_path, []):
        if any(data['file_path'].endswith(path) for path in possible_paths):
            return data['file_path']

    # Check across all modules if not found in the same module
    for module_data in codebase_data.values():
        for data in module_data:
            if any(data['file_path'].endswith(path) for path in possible_paths):
                return data['file_path']

    # Log warning if no path is resolved
    logging.warning(f"Unable to resolve import: {import_statement} from {file_path}")
    return None

def build_dependency_graph(codebase_data):
    graph = nx.DiGraph()
    for _, module_data in codebase_data.items():
        for file_data in module_data:
            try:
                graph.add_node(file_data['file_path'], language=file_data['language'])
                if file_data['language'] in ['python', 'javascript', 'typescript']:
                    for import_statement in file_data['analysis']['imports']:
                        resolved_import = resolve_import(import_statement, file_data['file_path'], codebase_data)
                        if resolved_import:
                            graph.add_edge(file_data['file_path'], resolved_import)
            except KeyError as e:
                logging.exception(f"Error building dependency graph: {str(e)}")
            except Exception as e:
                logging.exception(f"Unexpected error building dependency graph: {str(e)}")
    return graph

def visualize_dependency_graph(graph, output_dir):
    try:
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(graph, k=0.3, seed=42)
        languages = nx.get_node_attributes(graph, 'language')
        node_colors = ['skyblue' if lang == 'python' else 'lightgreen' if lang == 'javascript' else 'orange' for lang in languages.values()]
        nx.draw_networkx(graph, pos, with_labels=True, node_size=500, node_color=node_colors, font_size=10, edge_cmap=plt.cm.Blues)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'dependency_graph.png')
        plt.savefig(output_file)
        plt.close()
        logging.info(f"Dependency graph saved to {output_file}")
    except Exception as e:
        logging.exception(f"Error visualizing dependency graph: {str(e)}")

def build_call_graph(codebase_data):
    try:
        call_graph = nx.DiGraph()
        for module_data in codebase_data.values():
            for file_data in module_data:
                if file_data['language'] == 'python':
                    try:
                        analyzer = pyan.analyzer.CallGraphVisitor(filenames=[file_data['file_path']])
                        analyzer.analyze()
                        for caller, callee in analyzer.calls:
                            call_graph.add_edge(caller.name, callee.name)
                    except Exception as e:
                        logging.exception(f"Error building call graph for file: {file_data['file_path']}, Error: {str(e)}")
        return call_graph
    except Exception as e:
        logging.exception(f"Error building call graph: {str(e)}")
        return None

def visualize_call_graph(call_graph, output_dir):
    try:
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(call_graph, k=0.3, seed=42)
        nx.draw_networkx(call_graph, pos, with_labels=True, node_size=500, node_color='skyblue', font_size=10, edge_cmap=plt.cm.Blues)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'call_graph.png')
        plt.savefig(output_file)
        plt.close()
        logging.info(f"Call graph saved to {output_file}")
    except Exception as e:
        logging.exception(f"Error visualizing call graph: {str(e)}")

import unittest
from unittest.mock import patch, MagicMock
import networkx as nx
from graph_management import resolve_import, build_dependency_graph, visualize_dependency_graph, build_call_graph, visualize_call_graph

class TestGraphManagement(unittest.TestCase):
    def setUp(self):
        self.codebase_data = {
            'module1': [
                {'file_path': 'module1/file1.py', 'language': 'python', 'analysis': {'imports': ['module2.util']}},
                {'file_path': 'module1/main.js', 'language': 'javascript', 'analysis': {'imports': ['module2.feature']}},
                {'file_path': 'module1/style.css', 'language': 'css', 'analysis': {'imports': []}}
            ],
            'module2': [
                {'file_path': 'module2/util.js', 'language': 'javascript', 'analysis': {'imports': []}},
                {'file_path': 'module2/feature.ts', 'language': 'typescript', 'analysis': {'imports': []}}
            ]
        }

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('pyan.analyzer.CallGraphVisitor')
    def test_build_call_graph(self, mock_call_graph_visitor):
        # Mock the call graph analysis behavior
        mock_analyzer = MagicMock()
        mock_analyzer.calls = []
        mock_call_graph_visitor.return_value = mock_analyzer
        
        call_graph = build_call_graph(self.codebase_data)
        self.assertIsInstance(call_graph, nx.DiGraph)
        mock_call_graph_visitor.assert_called()

    @patch('os.makedirs')
    @patch('matplotlib.pyplot.savefig')
    def test_visualize_graphs(self, mock_savefig, mock_makedirs):
        dependency_graph = build_dependency_graph(self.codebase_data)
        output_dir = 'test_output'
        visualize_dependency_graph(dependency_graph, output_dir)
        mock_savefig.assert_called_once()
        mock_makedirs.assert_called_with(output_dir, exist_ok=True)

        call_graph = build_call_graph(self.codebase_data)
        visualize_call_graph(call_graph, output_dir)
        mock_savefig.assert_called()

    def test_resolve_import(self):
        resolved = resolve_import('module2.util', 'module1/main.js', self.codebase_data)
        self.assertEqual(resolved, 'module2/util.js')

        resolved = resolve_import('module2.feature', 'module1/main.js', self.codebase_data)
        self.assertEqual(resolved, 'module2/feature.ts')

        resolved = resolve_import('module2.missing', 'module1/main.js', self.codebase_data)
        self.assertIsNone(resolved)

if __name__ == '__main__':
    unittest.main()

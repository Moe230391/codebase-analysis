import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import ast
import asyncio
from analysis import (
    extract_docstrings_and_comments, analyze_function_calls, resolve_function_name,
    process_python_file, process_html_file, process_css_file, process_javascript_file,
    process_json_file, process_markdown_file, process_text_file, process_yaml_file,
    process_xml_file, process_image_file, process_document_file, process_typescript_file,
    process_jsx_file, process_vue_file, default_handler, analyze_lint_results,
    count_skipped_files
)

class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.nlp = MagicMock()

    def test_extract_docstrings_and_comments(self):
        code = '''
        def foo():
            """This is a docstring."""
            # This is a comment
            pass
        '''
        docstrings, comments = extract_docstrings_and_comments(code)
        self.assertEqual(docstrings, {'foo': 'This is a docstring.'})
        self.assertEqual(comments, ['# This is a comment'])

    def test_analyze_function_calls(self):
        code = '''
        def foo():
            bar()
            baz()
        '''
        tree = ast.parse(code)
        function_node = tree.body[0]
        call_graph = analyze_function_calls(function_node)
        self.assertIn(('foo', 'bar'), call_graph.edges)
        self.assertIn(('foo', 'baz'), call_graph.edges)

    def test_resolve_function_name(self):
        code = '''
        foo.bar()
        '''
        tree = ast.parse(code)
        call_node = tree.body[0].value
        function_name = resolve_function_name(call_node.func)
        self.assertEqual(function_name, 'bar')

    @patch('analysis.async_read')
    @patch('analysis.nlp')
    async def test_process_python_file(self, mock_nlp, mock_async_read):
        # Mock setup
        mock_async_read.return_value = asyncio.Future()
        mock_async_read.return_value.set_result('def foo(): pass')
    
        mock_nlp.return_value.ents = []
    
        # Execute the function under test
        data = await process_python_file('test.py', 'module1', 'python', mock_nlp)
    
        # Assertions to check if the function behaves as expected
        self.assertEqual(data['file_path'], 'test.py')
        self.assertEqual(data['language'], 'python')
        self.assertTrue('functions' in data['analysis'])  # Check if 'functions' key exists in analysis
        self.assertEqual(data['analysis']['functions'][0]['name'], 'foo')


    @patch('analysis.async_read')
    @patch('analysis.nlp')
    async def test_process_html_file(self, mock_nlp, mock_async_read):
        mock_async_read.return_value = '<html><body><h1>Test</h1></body></html>'
        mock_nlp.return_value.ents = []
        data = await process_html_file('test.html', 'module1', 'html', self.nlp)
        self.assertEqual(data['file_path'], 'test.html')
        self.assertEqual(data['language'], 'html')
        self.assertIn('h1', data['analysis']['tags'])

    @patch('analysis.async_read')
    @patch('analysis.nlp')
    async def test_process_css_file(self, mock_nlp, mock_async_read):
        mock_async_read.return_value = 'body { color: red; }'
        mock_nlp.return_value.ents = []
        data = await process_css_file('test.css', 'module1', 'css', self.nlp)
        self.assertEqual(data['file_path'], 'test.css')
        self.assertEqual(data['language'], 'css')
        self.assertIn('body', data['analysis']['rules'])

    @patch('analysis.async_read')
    @patch('analysis.nlp')
    async def test_process_javascript_file(self, mock_nlp, mock_async_read):
        mock_async_read.return_value = 'function foo() { console.log("Hello"); }'
        mock_nlp.return_value.ents = []
        data = await process_javascript_file('test.js', 'module1', 'javascript', self.nlp)
        self.assertEqual(data['file_path'], 'test.js')
        self.assertEqual(data['language'], 'javascript')
        self.assertEqual(data['analysis']['functions'][0]['name'], 'foo')

    @patch('analysis.async_read')
    @patch('analysis.nlp')
    async def test_process_json_file(self, mock_nlp, mock_async_read):
        mock_async_read.return_value = '{"key": "value"}'
        mock_nlp.return_value.ents = []
        data = await process_json_file('test.json', 'module1', 'json', self.nlp)
        self.assertEqual(data['file_path'], 'test.json')
        self.assertEqual(data['language'], 'json')
        self.assertEqual(data['analysis']['data'], {'key': 'value'})

    @patch('analysis.async_read')
    @patch('analysis.nlp')
    async def test_process_markdown_file(self, mock_nlp, mock_async_read):
        mock_async_read.return_value = '# Heading'
        mock_nlp.return_value.ents = []
        data = await process_markdown_file('test.md', 'module1', 'markdown', self.nlp)
        self.assertEqual(data['file_path'], 'test.md')
        self.assertEqual(data['language'], 'markdown')
        self.assertIn('<h1>Heading</h1>', data['analysis']['html'])

    @patch('analysis.async_read')
    @patch('analysis.nlp')
    async def test_process_text_file(self, mock_nlp, mock_async_read):
        mock_async_read.return_value = 'This is a plain text file.'
        mock_nlp.return_value.ents = []
        data = await process_text_file('test.txt', 'module1', 'text', self.nlp)
        self.assertEqual(data['file_path'], 'test.txt')
        self.assertEqual(data['language'], 'text')
        self.assertEqual(data['content'], 'This is a plain text file.')

    @patch('analysis.async_read')
    @patch('analysis.nlp')
    async def test_process_yaml_file(self, mock_nlp, mock_async_read):
        mock_async_read.return_value = 'key: value'
        mock_nlp.return_value.ents = []
        data = await process_yaml_file('test.yaml', 'module1', 'yaml', self.nlp)
        self.assertEqual(data['file_path'], 'test.yaml')
        self.assertEqual(data['language'], 'yaml')
        self.assertEqual(data['analysis']['data'], {'key': 'value'})

    @patch('analysis.async_read')
    @patch('analysis.nlp')
    async def test_process_xml_file(self, mock_nlp, mock_async_read):
        mock_async_read.return_value = '<root><element>value</element></root>'
        mock_nlp.return_value.ents = []
        data = await process_xml_file('test.xml', 'module1', 'xml', self.nlp)
        self.assertEqual(data['file_path'], 'test.xml')
        self.assertEqual(data['language'], 'xml')
        self.assertIn('element', data['analysis']['tags'])

    @patch('analysis.async_read', new_callable=AsyncMock)
    @patch('analysis.os.path.getsize')
    async def test_process_image_file(self, mock_getsize, mock_async_read):
        mock_getsize.return_value = 1024
        result = await process_image_file(self.file_path, self.module_path)
        self.assertIsNotNone(result)
        self.assertEqual(result['file_path'], self.file_path)
        self.assertEqual(result['language'], 'image')
        self.assertIsNone(result['content'])
        self.assertEqual(result['metadata']['size'], 1024)

    @patch('analysis.async_read', new_callable=AsyncMock)
    @patch('analysis.nlp', new_callable=AsyncMock)
    @patch('analysis.os.path.getsize')
    async def test_process_document_file(self, mock_getsize, mock_nlp, mock_async_read):
        mock_async_read.return_value = 'Document content'
        mock_getsize.return_value = 2048
        mock_nlp.return_value.ents = [MagicMock(text='entity1', label_='label1')]
        result = await process_document_file(self.file_path, self.module_path, 'document', self.nlp)
        self.assertIsNotNone(result)
        self.assertIn('entity1', result['analysis']['entities'][0]['text'])

    @patch('analysis.async_read', new_callable=AsyncMock)
    @patch('analysis.subprocess.run')
    @patch('analysis.cc_visit')
    @patch('analysis.os.path.getsize')
    async def test_process_typescript_file(self, mock_getsize, mock_cc_visit, mock_run, mock_async_read):
        mock_async_read.return_value = 'let x = 10;'
        mock_getsize.return_value = 50
        mock_cc_visit.return_value.total_complexity = 1
        mock_run.return_value = MagicMock(returncode=0, stdout=b'{"lint_results": []}')
        result = await process_typescript_file(self.file_path, self.module_path, 'typescript', self.nlp)
        self.assertIsNotNone(result)
        self.assertEqual(result['language'], 'typescript')

    @patch('analysis.async_read', new_callable=AsyncMock)
    @patch('analysis.subprocess.run')
    async def test_process_jsx_file(self, mock_run, mock_async_read):
        mock_async_read.return_value = 'const element = <h1>Hello, world!</h1>;'
        mock_run.return_value = MagicMock(returncode=0, stdout=b'{"jsx_analysis": "parsed"}')
        result = await process_jsx_file(self.file_path, self.module_path, 'jsx', self.nlp)
        self.assertIsNotNone(result)
        self.assertIn('jsx_analysis', result['analysis'])

    @patch('analysis.async_read', new_callable=AsyncMock)
    @patch('analysis.subprocess.run')
    async def test_process_vue_file(self, mock_run, mock_async_read):
        mock_async_read.return_value = '<template><div>{{ message }}</div></template>'
        mock_run.return_value = MagicMock(returncode=0, stdout=b'{"vue_analysis": "parsed"}')
        result = await process_vue_file(self.file_path, self.module_path, 'vue', self.nlp)
        self.assertIsNotNone(result)
        self.assertIn('vue_analysis', result['analysis'])

if __name__ == '__main__':
    unittest.main()
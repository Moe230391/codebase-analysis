import json
import unittest
from unittest.mock import MagicMock, mock_open, patch, call
from utilities import is_binary, save_to_jsonl, verify_jsonl, load_analysis_cache

class TestUtilities(unittest.TestCase):
    def test_is_binary(self):
        # Simulate a binary file by containing a null byte in binary read
        with patch('builtins.open', mock_open(read_data=b'\x00')):
            self.assertTrue(is_binary('binaryfile.exe'))
        
        # Simulate a text file by not containing any null bytes in text read
        with patch('builtins.open', mock_open(read_data=b'Text content')):
            self.assertFalse(is_binary('textfile.txt'))

    def test_save_to_jsonl(self):
        # Assume the JSON serialization and file writing works correctly
        mock_data = {'test': 'data'}
        with patch('builtins.open', mock_open()) as mocked_file:
            save_to_jsonl(mock_data, 'path/to/output.jsonl')
            calls = [
                call('{'),
                call('"test"'),
                call(': '),
                call('"data"'),
                call('}'),
                call('\n')
            ]
            mocked_file().write.assert_has_calls(calls, any_order=True)

    def test_verify_jsonl(self):
        # Setup the file with valid JSON content
        with patch('builtins.open', mock_open(read_data='{"key": "value"}\n')), \
             patch('pathlib.Path.touch'):
            self.assertTrue(verify_jsonl('output.jsonl'))

        # Setup the file with invalid JSON content
        with patch('builtins.open', mock_open(read_data='{"key": value}\n')), \
             patch('pathlib.Path.touch'):
            self.assertFalse(verify_jsonl('output.jsonl'))

    def test_load_analysis_cache(self):
        # Provide sample data that matches what might be read from a file
        sample_cache = {'file1.py': {'hash': 'abc123'}}
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_cache))), \
             patch('pathlib.Path.exists', return_value=True):
            cache = load_analysis_cache()
            self.assertEqual(cache, sample_cache)

if __name__ == '__main__':
    unittest.main()

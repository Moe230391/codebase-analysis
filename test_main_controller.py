import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from pathlib import Path
from main_controller import process_file, process_directory_concurrently, process_all_directories, calculate_codebase_stats, FILE_TYPE_HANDLERS, process_file_in_pool

class TestMainController(unittest.TestCase):
    def setUp(self):
        self.mock_nlp = MagicMock()
        self.mock_file_data = {
            'content': 'print("Hello, World!")',
            'language': 'python',
            'analysis': {
                'entities': [],
                'function_count': 1,
                'comment_density': 0.1
            }
        }

    @patch('main_controller.guess_file_type', new_callable=AsyncMock)
    @patch('main_controller.guess_language', new_callable=AsyncMock)
    @patch('main_controller.save_to_jsonl')
    async def test_process_file(self, mock_save_to_jsonl, mock_guess_language, mock_guess_file_type):
        mock_guess_file_type.return_value = '.py'
        mock_guess_language.return_value = 'python'
    
        with patch.dict('main_controller.FILE_TYPE_HANDLERS', {'.py': AsyncMock(return_value=self.mock_file_data)}):
            await process_file('test.py', 'module1', 'output_dir', self.mock_nlp)
        
        mock_save_to_jsonl.assert_called_once()
        FILE_TYPE_HANDLERS['.py'].assert_called_once_with('test.py', 'module1', 'python', self.mock_nlp)

    @patch('main_controller.process_file', new_callable=AsyncMock)
    def test_process_directory_concurrently(self, mock_process_file):
        test_dir = Path('test_dir')
        test_dir.mkdir(exist_ok=True)
        file1 = test_dir / 'file1.txt'
        file2 = test_dir / 'file2.txt'
        file1.touch()
        file2.touch()

        with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
            mock_executor.return_value.__enter__.return_value.map.return_value = None
            process_directory_concurrently(str(test_dir), str(test_dir.parent), 'output_dir', self.mock_nlp)
        
            file_paths = [p for p in test_dir.rglob('*') if p.is_file()]
            args_list = [(str(file_path), str(file_path.relative_to(test_dir)), 'output_dir', self.mock_nlp) for file_path in file_paths]
            mock_executor.return_value.__enter__.return_value.map.assert_called_once_with(process_file_in_pool, args_list)
        
            for args in args_list:
                mock_process_file.assert_any_call(*args)

        file1.unlink()
        file2.unlink()
        test_dir.rmdir()
    
    @patch('main_controller.process_directory_concurrently')
    def test_process_all_directories(self, mock_process_directory_concurrently):
        with patch('os.walk') as mock_walk:
            mock_walk.return_value = [('root', [], [])]
            process_all_directories('root_dir', 'output_dir', self.mock_nlp)
            mock_process_directory_concurrently.assert_called_once_with('root', 'root_dir', 'output_dir', self.mock_nlp)

    def test_calculate_codebase_stats(self):
        codebase_data = {
            'module1': [
                {
                    'language': 'python',
                    'metadata': {
                        'loc': 100,
                        'size': 1024
                    }
                }
            ]
        }
        stats = calculate_codebase_stats(codebase_data)
        self.assertEqual(stats['total_files'], 1)
        self.assertEqual(stats['total_loc'], 100)
        self.assertEqual(stats['total_size'], 1024)
        self.assertEqual(stats['files_by_language']['python'], 1)
        self.assertEqual(stats['loc_by_language']['python'], 100)
        self.assertEqual(stats['size_by_language']['python'], 1024)

if __name__ == '__main__':
    unittest.main()
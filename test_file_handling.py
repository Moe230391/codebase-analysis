import unittest
from unittest.mock import patch, MagicMock, AsyncMock

import pygments
from file_handling import guess_file_type, guess_language, is_text_file, is_binary_file, read_text_file, async_read

class TestFileHandling(unittest.TestCase):
    @patch('filetype.guess')
    @patch('magic.from_file')
    async def test_guess_file_type(self, mock_magic, mock_filetype_guess):
        mock_filetype_guess.return_value = MagicMock(mime='text/plain')
        file_type = await guess_file_type('test.txt')
        self.assertEqual(file_type, 'text/plain')

        mock_filetype_guess.return_value = None
        mock_magic.return_value = 'application/json'
        file_type = await guess_file_type('test.json')
        self.assertEqual(file_type, 'application/json')

    @patch('pygments.lexers.guess_lexer')
    @patch('pygments.lexers.get_lexer_for_filename')
    async def test_guess_language(self, mock_get_lexer, mock_guess_lexer):
        mock_lexer = MagicMock()
        mock_lexer.name = 'Python'
        mock_get_lexer.return_value = mock_lexer
        language = await guess_language('test.py')
        self.assertEqual(language, 'python')

        mock_get_lexer.side_effect = pygments.util.ClassNotFound
        mock_guess_lexer.return_value = mock_lexer
        language = await guess_language('test.py')
        self.assertEqual(language, 'python')

    @patch('file_handling.guess_file_type', new_callable=AsyncMock)
    async def test_is_text_file(self, mock_guess_file_type):
        mock_guess_file_type.return_value = 'text/plain'
        is_text = await is_text_file('test.txt')
        self.assertTrue(is_text)

        mock_guess_file_type.return_value = 'application/octet-stream'
        is_text = await is_text_file('test.bin')
        self.assertFalse(is_text)

    @patch('file_handling.guess_file_type', new_callable=AsyncMock)
    async def test_is_binary_file(self, mock_guess_file_type):
        mock_guess_file_type.return_value = 'application/octet-stream'
        is_binary = await is_binary_file('test.bin')
        self.assertTrue(is_binary)

        mock_guess_file_type.return_value = 'text/plain'
        is_binary = await is_binary_file('test.txt')
        self.assertFalse(is_binary)

    @patch('aiofiles.open', new_callable=AsyncMock)
    async def test_read_text_file(self, mock_open):
        mock_file = MagicMock()
        mock_file.read.return_value = 'File content'
        mock_open.return_value.__aenter__.return_value = mock_file
        content = await read_text_file('test.txt')
        self.assertEqual(content, 'File content')

    @patch('file_handling.is_binary_file', new_callable=AsyncMock)
    @patch('file_handling.read_text_file', new_callable=AsyncMock)
    async def test_async_read(self, mock_read_text_file, mock_is_binary_file):
        mock_is_binary_file.return_value = False
        mock_read_text_file.return_value = 'File content'
        content = await async_read('test.txt')
        self.assertEqual(content, 'File content')

        mock_is_binary_file.return_value = True
        content = await async_read('test.bin')
        self.assertIsNone(content)

if __name__ == '__main__':
    unittest.main()
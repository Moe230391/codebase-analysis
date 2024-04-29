import unittest
from data_validation import validate_json, validate_file_path, validate_language, validate_content, validate_analysis, validate_metadata, validate_data

class TestDataValidation(unittest.TestCase):
    def test_validate_json(self):
        # Test case 1: Valid JSON
        valid_json = {
            "file_path": "example.py",
            "language": "python",
            "content": "print('Hello, World!')",
            "analysis": {},
            "metadata": {"size": 24}
        }
        self.assertTrue(validate_json(valid_json))

        # Test case 2: Invalid JSON (missing required fields)
        invalid_json = {
            "file_path": "example.py",
            "language": "python",
            "content": "print('Hello, World!')"
        }
        self.assertFalse(validate_json(invalid_json))

    def test_validate_file_path(self):
        # Test case 1: Valid file path
        self.assertTrue(validate_file_path("example.py"))

        # Test case 2: Empty file path
        self.assertFalse(validate_file_path(""))

    def test_validate_language(self):
        # Test case 1: Valid language
        self.assertTrue(validate_language("python"))

        # Test case 2: Invalid language
        self.assertFalse(validate_language("invalid_language"))

    def test_validate_content(self):
        # Test case 1: Valid content
        self.assertTrue(validate_content("print('Hello, World!')"))

        # Test case 2: Empty content
        self.assertFalse(validate_content(""))

    def test_validate_analysis(self):
        # Test case 1: Valid analysis
        self.assertTrue(validate_analysis({"entities": []}))

        # Test case 2: Empty analysis
        self.assertTrue(validate_analysis({}))

    def test_validate_metadata(self):
        # Test case 1: Valid metadata
        self.assertTrue(validate_metadata({"size": 24}))

        # Test case 2: Missing size in metadata
        self.assertFalse(validate_metadata({"md5_hash": "abcdef"}))

    def test_validate_data(self):
        # Test case 1: Valid data
        valid_data = {
            "file_path": "example.py",
            "language": "python",
            "content": "print('Hello, World!')",
            "analysis": {},
            "metadata": {"size": 24}
        }
        self.assertTrue(validate_data(valid_data))

        # Test case 2: Invalid data (missing required fields)
        invalid_data = {
            "file_path": "example.py",
            "language": "python",
            "content": "print('Hello, World!')"
        }
        self.assertFalse(validate_data(invalid_data))

if __name__ == '__main__':
    unittest.main()
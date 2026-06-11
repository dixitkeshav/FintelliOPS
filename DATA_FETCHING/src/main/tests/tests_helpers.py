import unittest
import sys
import os

# Ensure the script can find 'src' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Now import the clean_text function
from src.main.utils.helpers import clean_text

class TestHelpers(unittest.TestCase):
    def test_clean_text(self):
        input_text = "<html>Breaking News: Market crashes!</html>"
        expected_output = "breaking news market crashes"
        self.assertEqual(clean_text(input_text), expected_output)

if __name__ == "__main__":
    unittest.main()

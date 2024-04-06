import unittest
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, './api')  # Replace with the actual path to the parent directory of api

from main import app 

# Create a test client using FastAPI's TestClient
client = TestClient(app)

class TestAPI(unittest.TestCase):

    def test_version_endpoint(self):
        # Test the version endpoint "/version/"
        response = client.get("/version/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("software_version", response.json())
        self.assertIn("data_version", response.json())
        
    def test_predictions_endpoint(self):
        # Test the version endpoint "/predictions/{date}/"
        response = client.get("/predictions/2024-01-05")
        self.assertEqual(response.status_code, 200)
        self.assertIn("predictions", response.json())
        
    def test_combined_predictions_endpoint(self):
        # Test the version endpoint "/combined_predictions/{start_date}/{end_date}/"
        response = client.get("/combined_predictions/2024-01-05/2024-01-10")
        self.assertEqual(response.status_code, 200)
        self.assertIn("predictions and true labels", response.json())


if __name__ == '__main__':
    unittest.main()



# unit-tests:
#   runs-on: ubuntu-latest

#   steps:
#     - name: Checkout code
#       uses: actions/checkout@v2

#     - name: Set up Python
#       uses: actions/setup-python@v2
#       with:
#         python-version: '3.12'

#     - name: Install dependencies
#       run: pip install -r requirements.txt

#     - name: Run unit tests
#       run: python -m unittest discover -s tests -p 'test_*.py'

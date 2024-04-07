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
        # Check if the keys are present in the data_version object
        data_version = response.json()["data_version"]
        expected_keys = ["latituude", "longitude", "start_date", "end_date"]
        for key in expected_keys:
            self.assertIn(key, data_version)
        
    def test_predictions_endpoint(self):
        # Test the version endpoint "/predictions/{date}/"
        response = client.get("/predictions/2024-01-05")
        self.assertEqual(response.status_code, 200)
        self.assertIn("predictions and true labels if they are", response.json())
        data = response.json()["predictions and true labels if they are"]
        expected_keys = ["predictions"] # can not check for true labels as there are none if the prediction is for a date in the future
        for key in expected_keys: 
            self.assertIn(key, data)
        self.assertGreaterEqual(len(data),1)
        
    def test_combined_predictions_endpoint(self):
        # Test the version endpoint "/combined_predictions/{start_date}/{end_date}/"
        response = client.get("/combined_predictions/2024-01-05/2024-01-10")
        self.assertEqual(response.status_code, 200)
        self.assertIn("predictions and true labels if they are", response.json())
        data = response.json()["predictions and true labels if they are"]
        self.assertGreaterEqual(len(data),1)
        expected_keys = ["predictions"] # can not check for true labels as there are none if the prediction is for a date in the future
        for key in expected_keys: 
            self.assertIn(key, data)
        self.assertGreaterEqual(len(data),1)


if __name__ == '__main__':
    unittest.main()


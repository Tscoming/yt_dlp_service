import unittest, requests, zipfile, io, os

class TestYtdlpApi(unittest.TestCase):
    """
    Test suite for the yt-dlp REST API.
    
    Ensure the API service is running before executing these tests.
    """
    
    BASE_URL = "http://127.0.0.1:9000/api/v1/youtube"
    TEST_VIDEO_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw" # "Me at the zoo" - The first video on YouTube, very short.
    
    def test_01_info_endpoint_success(self):
        """Tests the /info endpoint with a valid URL."""
        print("\n--- Testing /info endpoint ---")
        response = requests.post(f"{self.BASE_URL}/info", json={"url": self.TEST_VIDEO_URL})
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        print(f"Video Title: {data.get('title')}")
        self.assertIn("title", data)
        self.assertIn("video_id", data)
        self.assertEqual(data["video_id"], "jNQXAC9IVRw")
        self.assertIn("formats", data)
        self.assertTrue(isinstance(data["formats"], list))
        print("Test for /info endpoint PASSED.")

    def test_02_download_endpoint_success(self):
        """Tests the /download endpoint with a valid URL."""
        print("\n--- Testing /download endpoint ---")
        with requests.post(f"{self.BASE_URL}/download", json={"url": self.TEST_VIDEO_URL}, stream=True) as response:
            print(f"Status Code: {response.status_code}")
            self.assertEqual(response.status_code, 200)
            
            self.assertIn("application/zip", response.headers.get("Content-Type", ""))
            
            buffer = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192): buffer.write(chunk)
            buffer.seek(0) # Reset buffer's position to the beginning
            
            self.assertTrue(zipfile.is_zipfile(buffer)) # Check if it's a valid zip file
            
            with zipfile.ZipFile(buffer, 'r') as zf:
                file_list = zf.namelist()
                print(f"Files in zip: {file_list}")
                self.assertTrue(any(f.endswith(('.mp4', '.webm', '.mkv')) for f in file_list)) # We expect at least one video file.

            print("Test for /download endpoint PASSED.")

    def test_03_invalid_url(self):
        """Tests both endpoints with a deliberately invalid URL."""
        print("\n--- Testing invalid URL handling ---")
        invalid_url = "https://www.youtube.com/watch?v=invalidurlxyz"
        
        # Test /info
        response_info = requests.post(f"{self.BASE_URL}/info", json={"url": invalid_url})
        print(f"/info with invalid URL - Status Code: {response_info.status_code}")
        self.assertEqual(response_info.status_code, 500)

        # Test /download
        response_download = requests.post(f"{self.BASE_URL}/download", json={"url": invalid_url})
        print(f"/download with invalid URL - Status Code: {response_download.status_code}")
        self.assertEqual(response_download.status_code, 500)
        print("Test for invalid URL handling PASSED.")

if __name__ == "__main__":
    print("Starting API tests...")
    print(f"Targeting API at: {TestYtdlpApi.BASE_URL}")
    print(f"Using test video: {TestYtdlpApi.TEST_VIDEO_URL}")
    print("==========================================")
    
    try: # First, check if the server is running
        requests.get(TestYtdlpApi.BASE_URL.rsplit('/api', 1)[0] + "/docs")
    except requests.ConnectionError:
        print("\nERROR: API server is not running or not accessible at the specified URL.")
        print("Please start the server before running tests.")
        exit(1)
        
    unittest.main()

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

class TestBilibiliApi(unittest.TestCase):
    """Test suite for the Bilibili API endpoints."""
    
    BASE_URL = "http://127.0.0.1:9000/api/v1/bilibili"

    def test_get_zones_success(self):
        """Tests the /zones endpoint."""
        print("\n--- Testing /zones endpoint ---")
        response = requests.get(f"{self.BASE_URL}/zones")
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(isinstance(data, list))
        self.assertGreater(len(data), 0)
        
        # Check for expected keys in the first zone object
        first_zone = data[0]
        self.assertIn("tid", first_zone)
        self.assertIn("reid", first_zone)
        self.assertIn("name", first_zone)
        self.assertIn("parent_reid", first_zone) # Not in all, but good to check
        
        print("Test for /zones endpoint PASSED.")

class TestTranslateApi(unittest.TestCase):
    """Test suite for the Translate API endpoint."""

    BASE_URL = "http://127.0.0.1:9000/api/v1/translate"

    def test_chunks_endpoint_success(self):
        """Tests the /chunks endpoint."""
        print("\n--- Testing /chunks endpoint ---")
        response = requests.post(f"{self.BASE_URL}/chunks", json={}) # Assuming no body is needed for this simple test
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Chunks processed successfully")
        
        print("Test for /chunks endpoint PASSED.")

if __name__ == "__main__":
    print("Starting API tests...")
    print(f"Targeting YouTube API at: {TestYtdlpApi.BASE_URL}")
    print(f"Targeting Bilibili API at: {TestBilibiliApi.BASE_URL}")
    print(f"Targeting Translate API at: {TestTranslateApi.BASE_URL}")
    print(f"Using test video: {TestYtdlpApi.TEST_VIDEO_URL}")
    print("==========================================")
    
    try:
        # Check if the server is running by accessing the docs
        server_root_url = TestYtdlpApi.BASE_URL.rsplit('/api', 1)[0]
        requests.get(server_root_url + "/docs", timeout=5)
    except requests.ConnectionError:
        print("\nERROR: API server is not running or not accessible at the specified URL.")
        print("Please start the server before running tests.")
        exit(1)
        
    # Create a TestSuite and add tests from both classes
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestYtdlpApi))
    suite.addTest(unittest.makeSuite(TestBilibiliApi))
    suite.addTest(unittest.makeSuite(TestTranslateApi))
    
    # Run the test suite
    runner = unittest.TextTestRunner()
    runner.run(suite)

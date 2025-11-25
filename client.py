import argparse
import requests
import zipfile
import io
import os
import sys

def download_video_client(video_url: str, output_dir: str, subtitles: list = None, api_base_url: str = "http://127.0.0.1:9000/api/v1/video"):
    """
    Calls the video download API and extracts the contents to the specified directory.
    """
    download_endpoint = f"{api_base_url}/download"
    print(f"Attempting to download video from: {video_url}")
    print(f"API Endpoint: {download_endpoint}")
    print(f"Output directory: {output_dir}")
    if subtitles:
        print(f"Requesting subtitles: {', '.join(subtitles)}")

    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        payload = {"url": video_url}
        if subtitles:
            payload["subtitles"] = subtitles

        response = requests.post(download_endpoint, json=payload, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        # Check content type to ensure it's a zip file
        if "application/zip" not in response.headers.get("Content-Type", ""):
            print(f"Error: API did not return a zip file. Content-Type: {response.headers.get('Content-Type')}")
            print(f"API Response: {response.text}")
            return False

        # Get filename from headers, or use a default
        filename = "download.zip" # Default filename
        content_disposition = response.headers.get('Content-Disposition')
        if content_disposition:
            parts = content_disposition.split('filename=')
            if len(parts) > 1:
                filename = parts[1].strip('"')
        
        print(f"Received zip file: {filename}")

        # Read the content into a bytes buffer
        buffer = io.BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            buffer.write(chunk)
        buffer.seek(0) # Reset buffer's position to the beginning

        if not zipfile.is_zipfile(buffer):
            print("Error: Received file is not a valid zip archive.")
            return False
            
        # Extract the zip file
        with zipfile.ZipFile(buffer, 'r') as zf:
            zf.extractall(output_dir)
            print(f"Successfully extracted content to '{output_dir}/'")
            for file in zf.namelist():
                print(f"  - {file}")
        
        return True

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        try:
            error_data = response.json()
            print(f"API Error Message: {error_data.get('error', 'No specific error message provided.')}")
        except ValueError:
            print(f"API Response Content: {response.text}")
        return False
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
        print("Please ensure the API service is running and accessible at the specified URL.")
        return False
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
        return False
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected request error occurred: {req_err}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client to download video and related files via yt-dlp API.")
    parser.add_argument("video_url", help="The URL of the video to download.")
    parser.add_argument("output_dir", help="The directory to save the downloaded and extracted files.")
    parser.add_argument("--subtitles", help="Comma-separated list of subtitle languages to download (e.g., 'en,es').")
    parser.add_argument("--api_host", default="127.0.0.1", help="The host of the API service (default: 127.0.0.1).")
    parser.add_argument("--api_port", type=int, default=8000, help="The port of the API service (default: 8000).")
    
    args = parser.parse_args()

    subtitle_list = args.subtitles.split(',') if args.subtitles else None
    api_base = f"http://{args.api_host}:{args.api_port}/api/v1/video"

    success = download_video_client(args.video_url, args.output_dir, subtitles=subtitle_list, api_base_url=api_base)
    if success:
        print("\nDownload process completed successfully!")
    else:
        print("\nDownload process failed.")
        sys.exit(1)

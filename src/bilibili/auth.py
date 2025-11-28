import asyncio
import json
import os
from pathlib import Path
from bilibili_api import Credential
from bilibili_api.login_v2 import QrCodeLogin
from bilibili_api.exceptions import ApiException

# Define the path for storing credentials
CRED_FILE_PATH = Path(__file__).parent / "bilibili_credentials.json"

async def save_credential(credential: Credential, ac_time_value: str = None):
    """Saves the credential object and ac_time_value to a JSON file."""
    cred_data = {
        "sessdata": credential.sessdata,
        "bili_jct": credential.bili_jct,
        "buvid3": credential.buvid3,
        "dedeuserid": credential.dedeuserid,
        "ac_time_value": ac_time_value,
    }
    try:
        CRED_FILE_PATH.write_text(json.dumps(cred_data, indent=4), encoding='utf-8')
        print(f"Credential saved successfully to {CRED_FILE_PATH}")
    except IOError as e:
        print(f"Error saving credential file: {e}")

async def load_credential() -> tuple[Credential | None, str | None]:
    """Loads the credential object and ac_time_value from a JSON file."""
    if not CRED_FILE_PATH.exists():
        print("Credential file not found.")
        return None, None
    
    try:
        cred_data = json.loads(CRED_FILE_PATH.read_text(encoding='utf-8'))
        credential = Credential(
            sessdata=cred_data.get("sessdata"),
            bili_jct=cred_data.get("bili_jct"),
            buvid3=cred_data.get("buvid3"),
            dedeuserid=cred_data.get("dedeuserid"),
        )
        ac_time_value = cred_data.get("ac_time_value")
        return credential, ac_time_value
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading or parsing credential file: {e}")
        return None, None

async def refresh_credential(credential: Credential, ac_time_value: str) -> Credential | None:
    """
    Tries to refresh the credential using the stored ac_time_value.
    Returns the updated credential on success, None on failure.
    """
    print("Attempting to refresh credential...")
    
    if not credential or not ac_time_value:
        print("No credential or ac_time_value found. Cannot refresh.")
        return None
        
    try:
        setattr(credential, 'ac_time_value', ac_time_value)
        await credential.refresh()
        print("Credential refreshed successfully!")
        new_ac_time_value = getattr(credential, 'ac_time_value', None)
        await save_credential(credential, new_ac_time_value)
        return credential
    except ApiException as e:
        print(f"Failed to refresh credential: {e}. A new login is likely required.")
        return None

async def login_and_save_credential() -> Credential | None:
    """
    Initiates a QR code login process and saves the new credential.
    Returns the new credential on success, None on failure.
    """
    print("Please scan the QR code on the console to log in...")
    try:
        qr_login = QrCodeLogin()
        await qr_login.generate_qrcode()
        print(qr_login.get_qrcode_terminal())
        
        while not qr_login.has_done():
            await qr_login.check_state()
            await asyncio.sleep(1) # Poll every second

        credential = qr_login.get_credential()
        print("Login successful!")
        refresh_token = getattr(credential, 'ac_time_value', None)
        await save_credential(credential, refresh_token)
        return credential
    except ApiException as e:
        print(f"Login failed: {e}")
        return None

async def get_credential() -> Credential:
    """
    Gets a valid credential, attempting to load and refresh it.
    This is the main function to be used by other modules.
    """
    credential, refresh_token = await load_credential()

    if credential:
        # Verify if the credential is still valid.
        try:
            # is_valid() is a synchronous check, but let's be safe
            if await credential.check_valid():
                print("Loaded credential is valid.")
                return credential
            else:
                print("Credential expired, attempting to refresh.")
                refreshed_credential = await refresh_credential(credential, ac_time_value)
                if refreshed_credential:
                    return refreshed_credential
        except ApiException as e:
            print(f"Error checking credential validity, attempting refresh: {e}")
            refreshed_credential = await refresh_credential(credential, ac_time_value)
            if refreshed_credential:
                return refreshed_credential

    # If no valid credential could be loaded or refreshed
    print("No valid credential available.")
    raise Exception("No valid Bilibili credential. Please trigger a login via the API.")

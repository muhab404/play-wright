import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import os

# Hardcoded login and export info
username = "to.ebner"
password = "Metis4149"
# book_id = "978-3968901688"
download_folder = "/tmp"



# Scopes for Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']


FOLDER_ID = os.environ.get('FOLDER_ID')
if not FOLDER_ID:
    raise Exception("FOLDER_ID environment variable not set")


# Set the folder ID where you want to upload the file
# FOLDER_ID = '1dIa8wA85QdmE08Iy3nwZ-aii7MzeTA6v'  # Replace with the actual folder ID


def write_service_account_key():
    creds_json = os.environ.get("GOOGLE_CREDS_JSON")
    if creds_json:
        key_path = "/tmp/service-account-key.json"
        with open(key_path, "w") as f:
            f.write(creds_json)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    else:
        raise Exception("GOOGLE_CREDS_JSON environment variable not set")

def upload_to_drive(service, file_path, folder_id):
    """Upload file to Google Drive"""
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [FOLDER_ID]
    }
    
    # If folder_id is provided, upload to specific folder
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    media = MediaFileUpload(file_path, resumable=True)
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    print('File uploaded with ID:', file.get('id'))
    return file.get('id')

def export_book_data(username, password, book_id, download_dir, drive_service):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
            args=[
        "--disable-gpu",
        "--single-process",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ]
)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # 1. Go to login page
        page.goto("https://www.mc-metis.de/login")

        # 2. Fill login form
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)
        page.click('button#login')

        # 3. Wait for login to complete
        page.wait_for_load_state("networkidle")

        # 4. Open the trading panel
        page.click('span.glyphicon-shopping-cart')
        page.wait_for_load_state("networkidle")

        # 5. Search for book
        page.fill('input[field="quickSearch"]', book_id)
        page.press('input[field="quickSearch"]', 'Enter')
        page.wait_for_load_state("networkidle")

        # 6. Select "menge" option
        page.select_option('select.sort-selection', '1')

        # 7. Select period
        page.click('button.dp-ext-replace-button')
        page.wait_for_selector('#date-picker-dropdown-container', state='visible')
        page.click('//i[text()="Year to Date"]')
        page.wait_for_load_state('networkidle')

        # 8. Update view
        page.wait_for_selector('#tab-line > div.pull-right.clearfix > div:nth-child(1) > button', state='visible')
        page.click('#tab-line > div.pull-right.clearfix > div:nth-child(1) > button')

        # 9. Open export dropdown
        page.click('#toolbar-benchmark-spin-button > i')
        page.locator('a[data-ember-action="1012"]').click()

        # 10. Trigger download and wait for it
        with page.expect_download() as download_info:
            page.locator('i.glyphicon-cloud-download').nth(2).click()
            # Wait for the download button to be visible
            screenshot_path = "/tmp/debug_before_download.png"
            page.screenshot(path=screenshot_path)

            page.locator('i.glyphicon-cloud-download').nth(2).click()  # Actual download button

        download = download_info.value

        # Save to desired path
        download_path = Path(download_dir) / f"{book_id}_export.xlsx"
        download.save_as(str(download_path))

        # NEW: Upload to Google Drive
        try:
            print("🔄 Uploading to Google Drive...")
            # drive_service = authenticate_google_drive()
            file_id = upload_to_drive(drive_service, str(download_path), FOLDER_ID)
            print(f"✅ File uploaded to Google Drive with ID: {file_id}")
        except Exception as e:
            print(f"❌ Error uploading to Google Drive: {e}")

        print(f"✅ Downloaded file saved to: {download_path}")

        browser.close()



def lambda_handler(event, context):
    # export_book_data(username, password, book_id, download_folder)
    # return {"status": "success"}
    write_service_account_key()

    # Path to your service account key
    SERVICE_ACCOUNT_FILE = '/tmp/service-account-key.json'
    # Authenticate using the service account
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # Build the Drive service
    drive_service = build('drive', 'v3', credentials=credentials)
    try:
        book_id = event.get("queryStringParameters", {}).get("book_id")
        if not book_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing book_id"})
            }

        # Run your export function
        export_book_data(username, password, book_id, download_folder, drive_service)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Export started for book_id: {book_id}"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
# if __name__ == "__main__":
#     export_book_data(username, password, book_id, download_folder)
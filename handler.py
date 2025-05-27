import json
from pathlib import Path
from playwright.sync_api import sync_playwright

# Hardcoded login and export info
username = "to.ebner"
password = "Metis4149"
# book_id = "978-3968901688"
download_folder = "/tmp"

import boto3

def upload_to_s3(local_path, bucket, key):
    s3 = boto3.client('s3')
    s3.upload_file(local_path, bucket, key)

def export_book_data(username, password, book_id, download_dir):
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
            # Upload to S3
            upload_to_s3(
                screenshot_path,
                "playwright-lambda-fenction",  # Replace with your bucket name
                f"debug/{book_id}_before_download.png"
            )
            page.locator('i.glyphicon-cloud-download').nth(2).click()  # Actual download button

        download = download_info.value

        # Save to desired path
        download_path = Path(download_dir) / f"{book_id}_export.xlsx"
        download.save_as(str(download_path))
        # Upload to S3
        upload_to_s3(str(download_path), "playwright-lambda-fenction", f"exports/{book_id}_export.xlsx")

        print(f"✅ Downloaded file saved to: {download_path}")

        browser.close()


def lambda_handler(event, context):
    # export_book_data(username, password, book_id, download_folder)
    # return {"status": "success"}
    try:
        book_id = event.get("queryStringParameters", {}).get("book_id")
        if not book_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing book_id"})
            }

        # Run your export function
        export_book_data(username, password, book_id, download_folder)

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
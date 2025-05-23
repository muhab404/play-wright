from pathlib import Path
from playwright.sync_api import sync_playwright

# Hardcoded login and export info
username = "to.ebner"
password = "Metis4149"
book_id = "978-3968901688"
download_folder = "/tmp"

def export_book_data(username, password, book_id, download_dir):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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
            page.click('a.show-loading.btn-mc-white-blue')  # Actual download button

        download = download_info.value

        # Save to desired path
        download_path = Path(download_dir) / f"{book_id}_export.xlsx"
        download.save_as(str(download_path))

        print(f"✅ Downloaded file saved to: {download_path}")

        browser.close()


def lambda_handler(event, context):
    export_book_data(username, password, book_id, download_folder)
    return {"status": "success"}

# if __name__ == "__main__":
#     export_book_data(username, password, book_id, download_folder)
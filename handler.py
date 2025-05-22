from pathlib import Path
from playwright.sync_api import sync_playwright

def lambda_handler(event, context):
    username = event.get("username", "to.ebner")
    password = event.get("password", "Metis4149")
    book_id = event.get("book_id", "978-3968901688")
    download_dir = "/tmp"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto("https://www.mc-metis.de/login")
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)
        page.click('button#login')
        page.wait_for_load_state("networkidle")

        page.click('span.glyphicon-shopping-cart')
        page.wait_for_load_state("networkidle")

        page.fill('input[field="quickSearch"]', book_id)
        page.press('input[field="quickSearch"]', 'Enter')
        page.wait_for_load_state("networkidle")

        page.select_option('select.sort-selection', '1')
        page.click('button.dp-ext-replace-button')
        page.wait_for_selector('#date-picker-dropdown-container', state='visible')
        page.click('//i[text()="Year to Date"]')
        page.wait_for_load_state('networkidle')

        page.click('#tab-line > div.pull-right.clearfix > div:nth-child(1) > button')
        page.click('#toolbar-benchmark-spin-button > i')
        page.locator('a[data-ember-action="1012"]').click()

        with page.expect_download() as download_info:
            page.click('a.show-loading.btn-mc-white-blue')

        download = download_info.value
        download_path = Path(download_dir) / f"{book_id}_export.xlsx"
        download.save_as(str(download_path))

        browser.close()

    return {
        "statusCode": 200,
        "body": f"✅ File saved to {download_path}"
    }

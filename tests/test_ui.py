import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")
SELENIUM_REMOTE_URL = os.getenv("SELENIUM_REMOTE_URL")


def build_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    if SELENIUM_REMOTE_URL:
        return webdriver.Remote(command_executor=SELENIUM_REMOTE_URL, options=options)
    return webdriver.Chrome(options=options)


def test_frontend_sentiment():
    driver = build_driver()
    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 30)
        text_input = wait.until(EC.presence_of_element_located((By.ID, "text-input")))
        text_input.send_keys("This app is incredibly intuitive and has made my daily workflow dramatically more efficient")
        driver.find_element(By.ID, "submit-btn").click()
        result = wait.until(EC.presence_of_element_located((By.ID, "result-output")))
        wait.until(lambda d: result.text.strip() != "")
        output = result.text.strip()
        assert output
        assert ("POSITIVE" in output) or ("NEGATIVE" in output) or ("Confidence" in output)
    finally:
        driver.quit()

"""End-to-end browser tests with Selenium. They need Chrome; they are skipped if no browser can start."""
import threading
from unittest.mock import Mock

import pytest

pytest.importorskip("selenium")

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from werkzeug.serving import make_server

from app.api import create_app

LONG_BODY = "Version control keeps a history of every change."


@pytest.fixture(scope="module")
def base_url():
    """Run the real Flask app on a free port, with an in-memory database."""
    app = create_app({"DATABASE": ":memory:", "NOTIFIER": Mock()})
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture
def browser(base_url):
    options = webdriver.ChromeOptions()
    for flag in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1200,900"):
        options.add_argument(flag)
    try:
        driver = webdriver.Chrome(options=options)
    except WebDriverException as error:
        pytest.skip(f"Chrome could not start: {error.msg[:120]}")
    driver.implicitly_wait(0)
    driver.get(base_url)
    yield driver
    driver.quit()


def wait_for_text(driver, locator, text, timeout=8):
    WebDriverWait(driver, timeout).until(EC.text_to_be_present_in_element(locator, text))


def register(driver, base_url, name="Rafi", email="rafi@ruet.ac.bd"):
    """Use the separate registration page, then return to the home page."""
    driver.get(base_url + "/register")
    driver.find_element(By.ID, "author-name").send_keys(name)
    driver.find_element(By.ID, "author-email").send_keys(email)
    driver.find_element(By.ID, "author-btn").click()
    wait_for_text(driver, (By.ID, "author-status"), "Registered as")
    driver.find_element(By.ID, "continue-link").click()
    wait_for_text(driver, (By.ID, "who"), f"Writing as {name}")


def test_register_write_review_publish_and_comment(browser, base_url):
    register(browser, base_url)

    Select(browser.find_element(By.ID, "post-kind")).select_by_value("article")
    browser.find_element(By.ID, "post-title").send_keys("Why Git matters")
    browser.find_element(By.ID, "post-body").send_keys(LONG_BODY)
    browser.find_element(By.ID, "post-btn").click()
    wait_for_text(browser, (By.ID, "post-status"), "pending")
    wait_for_text(browser, (By.ID, "pending-list"), "Why Git matters")

    browser.find_element(By.CSS_SELECTOR, "#pending-list .approve-btn").click()
    wait_for_text(browser, (By.ID, "published-list"), "Why Git matters")
    assert browser.find_element(By.ID, "pending-list").text == ""
    # readers can read the content, not only the title
    assert LONG_BODY in browser.find_element(By.CSS_SELECTOR, "#published-list .content").text

    post = browser.find_element(By.CSS_SELECTOR, "#published-list .post-item")
    post.find_element(By.CSS_SELECTOR, ".comment-name").send_keys("Nusrat")
    post.find_element(By.CSS_SELECTOR, ".comment-text").send_keys("Nice post")
    post.find_element(By.CSS_SELECTOR, ".comment-btn").click()
    wait_for_text(browser, (By.CSS_SELECTOR, "#published-list .comment-list"), "Nusrat: Nice post")


def test_vlog_without_a_link_shows_an_error(browser, base_url):
    register(browser, base_url, "Tanvir", "tanvir@ruet.ac.bd")

    Select(browser.find_element(By.ID, "post-kind")).select_by_value("vlog")
    browser.find_element(By.ID, "post-title").send_keys("Orientation day")
    browser.find_element(By.ID, "post-btn").click()
    wait_for_text(browser, (By.ID, "post-status"), "Error")
    assert "video link" in browser.find_element(By.ID, "post-status").text


def test_writing_without_registering_asks_to_register(browser):
    browser.find_element(By.ID, "post-title").send_keys("Hello")
    browser.find_element(By.ID, "post-btn").click()
    wait_for_text(browser, (By.ID, "post-status"), "please register first")


def test_published_vlog_shows_a_watch_link(browser, base_url):
    register(browser, base_url, "Mithi", "mithi@ruet.ac.bd")
    Select(browser.find_element(By.ID, "post-kind")).select_by_value("vlog")
    browser.find_element(By.ID, "post-title").send_keys("Campus tour")
    browser.find_element(By.ID, "post-url").send_keys("https://youtu.be/abc")
    browser.find_element(By.ID, "post-btn").click()
    wait_for_text(browser, (By.ID, "pending-list"), "Campus tour")
    browser.find_element(By.CSS_SELECTOR, "#pending-list .approve-btn").click()
    wait_for_text(browser, (By.ID, "published-list"), "Campus tour")
    link = browser.find_element(By.CSS_SELECTOR, "#published-list .video-link")
    assert link.get_attribute("href") == "https://youtu.be/abc"

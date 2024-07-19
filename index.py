from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import requests
import os
import getpass
import re
from datetime import datetime, timezone

def extract_unix_timestamp_from_urn(urn):
    postId = int(urn)
    timestamp = postId >> 22  # Shift right by 22 bits to get the timestamp (adjusting from 23 bits)
    return timestamp

def unix_timestamp_to_human_date(timestamp):
    utc_date = datetime.fromtimestamp(timestamp / 1000, timezone.utc)
    return utc_date.strftime('%a, %d %b %Y %H:%M:%S GMT (UTC)')

def get_utc_date_from_urn(urn):
    unix_timestamp = extract_unix_timestamp_from_urn(urn)
    return unix_timestamp_to_human_date(unix_timestamp)
def convert_date(date_str):
    # Parse the input date string to a datetime object
    dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT (UTC)")
    # Format the datetime object to the desired output format
    return dt.strftime("%Y-%m-%d %H:%M:%S")

getName = lambda s: s.split('\n')[0]
getTime = lambda s: ''.join(re.findall(r'\d+', s))

def login_to_linkedin(driver, email, password):
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))

    email_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")
    login_button = driver.find_element(By.XPATH, '//*[@type="submit"]')

    email_field.send_keys(email)
    password_field.send_keys(password)
    login_button.click()
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "captcha-internal")))
        print("CAPTCHA detected. Please solve it manually.")
        input("Press Enter after solving the CAPTCHA...")
    except:
        pass

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "global-nav")))

def load_all_posts(driver, scroll_pause_time=2, scroll_increment=700):
    last_height = driver.execute_script("return document.body.scrollHeight")
    current_height = 0

    while current_height < last_height:
        driver.execute_script(f"window.scrollTo(0, {current_height});")
        time.sleep(scroll_pause_time)
        current_height += scroll_increment
        last_height = driver.execute_script("return document.body.scrollHeight")
    print("Finished scrolling and loading posts")

def extract_posts(driver):
    post_data = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    current_height = 0

    while current_height < last_height:
        posts = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.pv0.ph5 > div > div > div.scaffold-finite-scroll__content > ul > li"))
        )

        for index, post in enumerate(posts):
            try:
                post_time = post.find_element(By.CSS_SELECTOR, "div.feed-shared-update-v2.feed-shared-update-v2--minimal-padding.full-height.relative.feed-shared-update-v2--e2e.feed-shared-update-v2--wrapped, div.feed-shared-update-v2.feed-shared-update-v2--minimal-padding.full-height.relative.feed-shared-update-v2--wrapped").get_attribute("data-urn")
                
            except:
                post_time = ""

            try:
                post_content = post.find_element(By.CSS_SELECTOR, "div.update-components-text.relative.update-components-update-v2__commentary span span[dir='ltr']").text
            except:
                post_content = ""

            try:
                post_date = post.find_element(By.CSS_SELECTOR, "a.app-aware-link.update-components-actor__sub-description-link span.update-components-actor__sub-description span").text
            except:
                post_date = ""

            try:
                post_image = post.find_element(By.CSS_SELECTOR, "img.ivm-view-attr__img--centered:not(.EntityPhoto-circle-3)").get_attribute("src")
            except:
                post_image = ""

            try:
                reactions_count = post.find_element(By.CSS_SELECTOR, 'button[aria-label$="reactions"] span').text
            except:
                reactions_count = ""

            try:
                comments_count = post.find_element(By.CSS_SELECTOR, 'button[aria-label$="comments"] span').text
            except:
                comments_count = ""
            try:
                shared_post = post.find_element(By.CSS_SELECTOR, "#fie-impression-container > div.update-components-mini-update-v2.feed-shared-update-v2__update-content-wrapper.artdeco-card > div.update-components-actor.display-flex.pt3 > div > div > a.app-aware-link.update-components-actor__meta-link > span.update-components-actor__title > span > span").text
            except:
                shared_post = ""
            try:
               post_link = post.find_element(By.CSS_SELECTOR, "#fie-impression-container > div.update-components-mini-update-v2.feed-shared-update-v2__update-content-wrapper.artdeco-card > div.mr2 a").get_attribute("href")
            except:
                post_link = ""

            post_data.append({
                "postTime": convert_date(get_utc_date_from_urn(getTime(post_time))) ,
                "content": post_content,
                "date": post_date,
                "image": post_image,
                "likes": reactions_count,
                "commentsCount": comments_count,
                "sharedBy":getName(shared_post),
                "sharedLink":post_link,
            })


        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    return post_data

def download_image(url, img_name):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            directory = "./images"
            if not os.path.exists(directory):
                os.makedirs(directory)
            img_path = os.path.join(directory, f"post{img_name}Img.jpg")
            with open(img_path, 'wb') as file:
                file.write(response.content)
            print(f"Finished downloading {img_path}")
        else:
            print(f"Failed to download image: {url}")
    except Exception as e:
        print(f"Error while downloading image: {url}. Error: {e}")

if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    email = input("Enter your LinkedIn email: ")
    password = getpass.getpass("Enter your LinkedIn password: ")
    login_to_linkedin(driver, email, password)

    profile_url = "https://www.linkedin.com/in/imhashir/recent-activity/all/"
    driver.get(profile_url)

    load_all_posts(driver)
    post_data = extract_posts(driver)

    # for index, post in enumerate(post_data):
    #     if post["image"]:
    #         download_image(post["image"], index + 1)

    with open('linkedin_posts.json', 'w') as file:
        json.dump(post_data, file, indent=4)

    driver.quit()


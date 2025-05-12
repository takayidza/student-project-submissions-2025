import random
import time
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from sentiment.models.social_media import SocialMediaComment, SocialMediaPost
import threading
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class Command(BaseCommand):
    help = "Fetch Facebook posts and comments and store them in the database"


    def initialize_browser(self):
        print("Initializing browser...")
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()

        # Create a temporary directory for user data (to avoid conflicts)
        user_data_dir = tempfile.mkdtemp()
        options.add_argument(f"user-data-dir={user_data_dir}")  # Use a unique temporary directory

        # Optional user-agent string to mimic a real browser
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36")
        options.add_argument("--incognito")  # Launch Chrome in incognito mode

        # Initialize the WebDriver with the specified options
        driver = webdriver.Chrome(service=service, options=options)
        print("Browser initialized successfully.")
        return driver


    def facebook_login(self, driver, email, password):
        try:
            print("Logging in to Facebook...")
            driver.get("https://www.facebook.com")
            time.sleep(random.uniform(5, 8))  # Wait for the page to load

            # Find input fields
            email_input = driver.find_element(By.ID, "email")  # Email field
            password_input = driver.find_element(By.ID, "pass")  # Password field
            email_input.send_keys(email)
            time.sleep(random.uniform(3, 5))
            password_input.send_keys(password)
            time.sleep(random.uniform(3, 5))

            # Click the login button
            login_button = driver.find_element(By.NAME, "login")
            login_button.click()
            time.sleep(random.uniform(8, 12))
            print("Login attempt completed.")
        except NoSuchElementException as e:
            print(f"Element not found during login: {e}")
        except Exception as e:
            print(f"Unexpected error during login: {e}")

    def calculate_max_posts(self, start_date, end_date):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        days_diff = (end_date - start_date).days

        if days_diff < 1:
            return 2
        elif days_diff <= 7:
            return random.randint(4, 8)
        elif days_diff <= 14:
            return random.randint(8, 12)
        elif days_diff <= 30:
            return random.randint(15, 18)
        else:
            return random.randint(20, 25)

    def scroll_and_scrape(self, driver, max_posts):
        captions = []
        image_urls = []
        comments = []
        reactions = []
        post_dates = []

        while len(captions) < max_posts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)

            posts = driver.find_elements(By.CSS_SELECTOR, "div.xu06os2.x1ok221b")
            for post in posts:
                if len(captions) >= max_posts:
                    break

                # Scrape caption
                try:
                    caption = post.find_element(By.CSS_SELECTOR, "div.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.x1vvkbs.x126k92a > div[dir='auto']").text
                    captions.append(caption)
                except Exception:
                    pass

                # Scrape image URLs
                try:
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    post_divs = soup.find_all("div", class_="x6s0dn4 x1jx94hy x78zum5 xdt5ytf x6ikm8r x10wlt62 x1n2onr6 xh8yej3")
                    for post_div in post_divs:
                        image = post_div.find("img")
                        image_url = image['src'] if image else None
                        if image_url:
                            image_urls.append(image_url)
                except Exception:
                    image_urls.append(None)

                # Scrape comments
                try:
                    soup = BeautifulSoup(post.get_attribute('outerHTML'), 'html.parser')
                    comment_elements = soup.find_all("div", class_="x1lliihq xjkvuk6 x1iorvi4")
                    post_comments = [comment.text for comment in comment_elements if comment.text]
                    comments.append(post_comments)
                except Exception:
                    comments.append([])

                # Scrape reactions
                try:
                    reaction_elements = post.find_elements(By.CSS_SELECTOR, "div[aria-label]")
                    post_reactions = {}
                    for element in reaction_elements:
                        aria_label = element.get_attribute("aria-label")
                        if aria_label:
                            parts = aria_label.split(":")
                            if len(parts) == 2:
                                reaction_type = parts[0].strip()
                                count = parts[1].strip().split()[0]
                                if reaction_type in ["Love", "Like", "Care", "Haha", "Sad", "Angry", "Wow"]:
                                    post_reactions[reaction_type] = int(count)
                    reactions.append(post_reactions)
                except Exception:
                    reactions.append({})

                # Scrape post date
                try:
                    date_element = post.find_element(By.CSS_SELECTOR, "span.x4k7w5x.x1h91t0o.x1h9r5lt")
                    date_text = date_element.text.strip().lower()
                    post_dates.append(date_text)
                except Exception:
                    post_dates.append(None)

        return captions, image_urls, comments, reactions, post_dates

    def save_to_database(self, captions, image_urls, comments, reactions, post_dates):
        for idx in range(len(captions)):
            post_obj, created = SocialMediaPost.objects.get_or_create(
                platform="facebook",
                post_id=f"post_{idx + 1}",
                defaults={
                    "message": captions[idx],
                    "created_time": parse_datetime(post_dates[idx]) if post_dates[idx] else None,
                },
            )
            
            # Store comments
            for comment in comments[idx]:
                SocialMediaComment.objects.get_or_create(
                    post=post_obj,
                    comment_id=f"comment_{random.randint(1000, 9999)}",  # Generate a random comment ID
                    defaults={
                        "text": comment,
                        "created_time": parse_datetime(post_dates[idx]) if post_dates[idx] else None,
                    },
                )

        print(f"Successfully stored {len(captions)} posts and comments in the database.")

    def handle(self, *args, **kwargs):
        # Initialize browser and perform scraping
        driver = self.initialize_browser()
        
        # Login to Facebook (replace with actual credentials)
        email = "anonymousmist21@gmail.com"  # Replace with your Facebook email
        password = "Mist@123"  # Replace with your Facebook password
        self.facebook_login(driver, email, password)
        
        url = "https://www.facebook.com/profile.php?id=100068158728213"  # Replace with your target URL
        start_date = "2025-01-01"  # Start date for scraping
        end_date = "2025-01-10"  # End date for scraping
        max_posts = self.calculate_max_posts(start_date, end_date)

        # Open Facebook page and scrape data
        driver.get(url)
        time.sleep(20)

        captions, image_urls, comments, reactions, post_dates = self.scroll_and_scrape(driver, max_posts)

        # Save the scraped data to the database
        self.save_to_database(captions, image_urls, comments, reactions, post_dates)

        # Close the browser after scraping
        driver.quit()
        self.stdout.write(self.style.SUCCESS("Successfully fetched and stored social media data."))

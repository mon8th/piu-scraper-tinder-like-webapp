# Alternative approach using Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import os
import requests
from urllib.parse import urljoin
import re

def scrape_with_selenium():
    options = Options()
    options.add_argument('--headless')
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        student_id = "210402033"
        url = f"https://my.paragoniu.edu.kh/qr?student_id={student_id}"
        browser.get(url)
        time.sleep(10)  # Wait for page to fully load
        
        # Now extract the data from the rendered page
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract student information
        student_data = {}
        
        # Find all table rows in the data table
        table_rows = soup.select(".v-data-table table tbody tr")
        
        # If that doesn't work, try alternative selectors
        if not table_rows:
            table_rows = soup.select(".key-value-table tr")
        
        if not table_rows:
            print("Could not find table rows. Debug info:")
            print(f"Number of tables found: {len(soup.find_all('table'))}")
            print(f"Number of elements with v-data-table class: {len(soup.select('.v-data-table'))}")
            
        # Process each row to extract key-value pairs
        for row in table_rows:
            cells = row.find_all('td')
            if len(cells) == 2:  # Key-value pair
                key = cells[0].text.strip()
                value = cells[1].text.strip()
                student_data[key] = value
        
        # Try to find profile picture
        profile_image_url = None
        
        # NEW METHOD: Look for background images in style attributes
        elements_with_style = soup.select('[style*="background-image"]')
        for element in elements_with_style:
            style = element.get('style', '')
            if 'background-image' in style:
                # Extract URL from css background-image: url("https://example.com/image.jpg")
                match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                if match:
                    profile_image_url = match.group(1)
                    print(f"Found background image: {profile_image_url}")
                    break
        
        # If still not found, try other methods
        if not profile_image_url:
            # Method 1: Look for image with common profile picture classes
            img_elements = soup.select("img.profile-image, img.avatar, img.student-photo")
            if img_elements:
                profile_image_url = img_elements[0].get('src')
            
            # Method 2: Look for any image in header/profile section
            if not profile_image_url:
                header_sections = soup.select("header, .profile-header, .student-profile, .v-card__title")
                for section in header_sections:
                    imgs = section.find_all('img')
                    if imgs:
                        profile_image_url = imgs[0].get('src')
                        break
            
            # Method 3: Last resort - get any image
            if not profile_image_url:
                all_imgs = soup.find_all('img')
                if all_imgs:
                    # Filter out small icons (likely not profile pictures)
                    potential_profile_pics = [img.get('src') for img in all_imgs 
                                             if img.get('width') is None or int(img.get('width', 0)) > 50]
                    if potential_profile_pics:
                        profile_image_url = potential_profile_pics[0]
        
        # Download profile picture if found
        if profile_image_url:
            # Handle relative URLs
            if profile_image_url.startswith('/'):
                profile_image_url = urljoin(url, profile_image_url)
                
            # Create folder if it doesn't exist
            os.makedirs('profile_pictures', exist_ok=True)
            
            # Download image
            try:
                img_response = requests.get(profile_image_url)
                if img_response.status_code == 200:
                    # Use a simple filename instead of parsing the URL
                    filename = f'profile_pictures/{student_id}.jpg'
                    
                    with open(filename, 'wb') as f:
                        f.write(img_response.content)
                    print(f"Profile picture saved to {filename}")
                    student_data['profile_picture_path'] = filename
                else:
                    print(f"Failed to download profile picture: HTTP {img_response.status_code}")
            except Exception as e:
                print(f"Error downloading profile picture: {e}")
        else:
            print("No profile picture found")
        
        # Print extracted data
        print("\nExtracted Student Information:")
        print(f"Name: {student_data.get('Name', 'Not found')}")
        print(f"ID Number: {student_data.get('ID Number', 'Not found')}")
        print(f"Faculty: {student_data.get('Faculty', 'Not found')}")
        print(f"Department: {student_data.get('Department', 'Not found')}")
        print(f"Enrollment Status: {student_data.get('Enrollment Status', 'Not found')}")
        
        return student_data
    finally:
        browser.quit()

if __name__ == "__main__":
    result = scrape_with_selenium()
    if result and all(k in result for k in ['Name', 'ID Number', 'Faculty', 'Department']):
        print("\nScraping completed successfully!")
    else:
        print("\nScraping incomplete or failed.")
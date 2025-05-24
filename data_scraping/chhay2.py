from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import os 
import requests
import re
from urllib.parse import urljoin
import csv
import json

FACILITIES = {
    '01': {'name': 'Engineering', 'departments': {
        '01': 'CE',
        '03': 'ARC',
        '05': 'IE'
    }},
    '02': {'name': 'Information Technology', 'departments': {
        '01': 'CS',
        '02': 'DAD',
        '03': 'MIS'
    }},
    '04': {'name': 'Economics and Administrative Sciences', 'departments': {
        '01': 'BAF',
        '02': 'BUS',
        '03': 'IR',
        '04': 'ITL'
    }}
}

def create_student_ids(years, student_max=35):
    student_ids = []
    for year in years:
        for facil_code, facil_info in FACILITIES.items():
            for dept_code, dept_name in facil_info['departments'].items(): 
                for i in range(1, student_max + 1):
                    student_id = f"{year}{facil_code}{dept_code}{i:03d}"
                    student_ids.append(student_id)
    return student_ids

def scrape_student(student_id):
    options = Options()
    options.add_argument('--headless')
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try: 
        url = f"https://my.paragoniu.edu.kh/qr?student_id={student_id}" 
        browser.get(url)
        time.sleep(10)  
        
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        student_data = {'student_id': student_id}  
        
        table_rows = soup.select(".v-data-table table tbody tr")
        if not table_rows:
            table_rows = soup.select(".key-value-table tr")
        
        for row in table_rows:
            cells = row.find_all('td')
            if len(cells) == 2:
                key = cells[0].text.strip()
                value = cells[1].text.strip()
                student_data[key] = value
        
        if len(student_data) == 1:
            print(f"Failed to scrape data for student ID: {student_id}")
            return None
        
        profile_image_url = None
        elements_with_style = soup.select('[style*="background-image"]')
        for element in elements_with_style:
            style = element.get('style', '')
            if 'background-image' in style:
                match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                if match:
                    profile_image_url = match.group(1)
                    break
        
        if profile_image_url:
            if profile_image_url.startswith('/'):
                profile_image_url = urljoin(url, profile_image_url)
                
            os.makedirs('images', exist_ok=True)
            image_path = os.path.join('images', f"{student_id}.jpg") 
            if not os.path.exists(image_path):
                response = requests.get(profile_image_url)
                if response.status_code == 200:
                    with open(image_path, 'wb') as file:
                        file.write(response.content)
                    student_data['profile_picture_path'] = image_path 
                else:
                    print(f"Failed to download image for student ID: {student_id}")
        else:
            print(f"No profile image found for student ID: {student_id}")
        
        print("\nExtracted Student Information:")
        print(f"Name: {student_data.get('Name', 'Not found')}")
        print(f"ID Number: {student_data.get('ID Number', 'Not found')}")
        print(f"Faculty: {student_data.get('Faculty', 'Not found')}")
        print(f"Department: {student_data.get('Department', 'Not found')}")
        print(f"Enrollment Status: {student_data.get('Enrollment Status', 'Not found')}")
        return student_data
            
    finally: 
        browser.quit()

def save_csv(results, filename='students.csv'):
    if not results or len(results) == 0:
        print("No data to save.")
        return
    
    # Fixed: handle fieldnames properly
    all_fields = set()
    for result in results:
        if result:
            all_fields.update(result.keys())
    
    fieldnames = list(all_fields)
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            if result:
                writer.writerow(result)
    print(f"Data saved to {filename}")
            
def main():
    years = ['21', '22'] 
    student_max = 5  
    
    student_ids = create_student_ids(years, student_max)
    print(f"Generated {len(student_ids)} student IDs.")
    
    results = []
    for student_id in student_ids:
        print(f"Scraping data for student ID: {student_id}")
        result = scrape_student(student_id)  
        if result:
            results.append(result)
        
        time.sleep(1)  
        
    save_csv(results)
    
    with open('student_data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"Scraped {len(results)} students successfully out of {len(student_ids)} attempts")

if __name__ == "__main__":
    main()
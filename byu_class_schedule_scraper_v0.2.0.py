#!/usr/bin/env python3
import sys
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def fetch_schedule():
    """Fetch schedule from BYU class schedule website"""
    print("Setting up Chrome driver...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
    except Exception as e:
        print(f"Failed to setup Chrome driver: {e}")
        return []
    
    results = []
    
    try:
        print("Accessing BYU class schedule...")
        driver.get("https://enrollment.byu.edu/schedule/class")
        
        print("Waiting for page to load...")
        time.sleep(5)
        
        # Try to find and fill the form
        try:
            # Look for term selector
            term_select = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "term"))
            )
            term_select.send_keys("20261")  # Winter 2026
            print("Selected Winter 2026 term")
        except:
            print("Could not find term selector, trying alternative approach...")
            # Try alternative selectors
            try:
                term_select = driver.find_element(By.NAME, "term")
                term_select.send_keys("20261")
                print("Found term selector by name")
            except:
                print("Term selector not found")
        
        try:
            # Look for subject field
            subject_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "subject"))
            )
            subject_input.send_keys("MATH")
            print("Entered MATH subject")
        except:
            print("Could not find subject field")
        
        try:
            # Look for course number field
            course_input = driver.find_element(By.ID, "catalog_nbr")
            course_input.send_keys("451")
            print("Entered course 451")
        except:
            print("Could not find course number field")
        
        # Try to submit the form
        try:
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            print("Clicked submit button")
        except:
            try:
                submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                submit_button.click()
                print("Clicked submit input")
            except:
                print("Could not find submit button")
        
        print("Waiting for results...")
        time.sleep(10)
        
        # Try to find results table
        try:
            results_table = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.datadisplaytable"))
            )
            print("Found results table")
        except:
            print("Results table not found, checking page source...")
            page_source = driver.page_source
            if "Conner" in page_source:
                print("Found 'Conner' in page source")
            if "MATH 451" in page_source:
                print("Found 'MATH 451' in page source")
            if "Winter 2026" in page_source:
                print("Found 'Winter 2026' in page source")
        
        # Extract schedule information
        print("Extracting schedule data...")
        rows = driver.find_elements(By.CSS_SELECTOR, "table.datadisplaytable tr")
        print(f"Found {len(rows)} table rows")
        
        for i, row in enumerate(rows):
            if i < 2:  # Skip header rows
                continue
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 10:
                try:
                    instructor = cells[6].text.strip()
                    if "Conner" in instructor:
                        days = cells[8].text.strip()
                        class_time = cells[9].text.strip()
                        location = cells[11].text.strip()
                        
                        results.append({
                            "instructor": instructor,
                            "days": days,
                            "time": class_time,
                            "location": location
                        })
                        print(f"Found Conner's section: {days} {class_time} {location}")
                except Exception as e:
                    print(f"Error processing row {i}: {e}")
        
        if not results:
            print("No results found, checking for any MATH 451 sections...")
            for i, row in enumerate(rows):
                if i < 2:
                    continue
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) > 10:
                    try:
                        course_info = cells[0].text.strip()
                        if "451" in course_info:
                            instructor = cells[6].text.strip()
                            days = cells[8].text.strip()
                            class_time = cells[9].text.strip()
                            location = cells[11].text.strip()
                            
                            results.append({
                                "instructor": instructor,
                                "days": days,
                                "time": class_time,
                                "location": location
                            })
                            print(f"Found MATH 451 section: {instructor} {days} {class_time} {location}")
                    except Exception as e:
                        print(f"Error processing row {i}: {e}")
    
    except Exception as e:
        print(f"Error during scraping: {str(e)}", file=sys.stderr)
    finally:
        driver.quit()
    
    return results

def main():
    """Main function"""
    print("Starting BYU class schedule scraper...")
    results = fetch_schedule()
    
    output = {"ok": bool(results), "results": results}
    
    # Save results to file
    with open("byu_math451_winter2026_schedule.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nScraping completed. Found {len(results)} results.")
    print(json.dumps(output, indent=2))
    
    if results:
        print("\nSchedule found! Proceeding to generate grid...")
    else:
        print("\nNo schedule found. Will use fallback MWF schedule.")

if __name__ == "__main__":
    main()

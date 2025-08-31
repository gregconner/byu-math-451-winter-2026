#!/usr/bin/env python3
import sys
import json
import time
import requests
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
        # Try the commtech URL first since it returned data
        driver.get("https://commtech.byu.edu/noauth/classSchedule/index.php")
        
        print("Waiting for page to load...")
        time.sleep(5)
        
        # Check if we can find any form elements
        try:
            # Look for search form
            search_form = driver.find_element(By.TAG_NAME, "form")
            print("Found search form")
            
            # Look for input fields
            inputs = driver.find_elements(By.TAG_NAME, "input")
            selects = driver.find_elements(By.TAG_NAME, "select")
            
            print(f"Found {len(inputs)} input fields and {len(selects)} select fields")
            
            # Try to find term selector
            term_found = False
            for select in selects:
                try:
                    options = select.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        if "2026" in option.text or "Winter" in option.text:
                            print(f"Found term option: {option.text}")
                            term_found = True
                            break
                except:
                    continue
            
            if not term_found:
                print("No Winter 2026 term found in dropdowns")
            
            # Look for subject/course fields
            for input_field in inputs:
                try:
                    placeholder = input_field.get_attribute("placeholder")
                    name = input_field.get_attribute("name")
                    id_attr = input_field.get_attribute("id")
                    print(f"Input field: name={name}, id={id_attr}, placeholder={placeholder}")
                except:
                    continue
                    
        except Exception as e:
            print(f"Error examining form: {e}")
        
        # Try to search for MATH 451
        try:
            # Look for subject field
            subject_field = None
            for input_field in inputs:
                try:
                    placeholder = input_field.get_attribute("placeholder")
                    if placeholder and ("subject" in placeholder.lower() or "dept" in placeholder.lower()):
                        subject_field = input_field
                        break
                except:
                    continue
            
            if subject_field:
                print("Found subject field, entering MATH")
                subject_field.send_keys("MATH")
            else:
                print("Subject field not found")
            
            # Look for course number field
            course_field = None
            for input_field in inputs:
                try:
                    placeholder = input_field.get_attribute("placeholder")
                    if placeholder and ("course" in placeholder.lower() or "number" in placeholder.lower()):
                        course_field = input_field
                        break
                except:
                    continue
            
            if course_field:
                print("Found course field, entering 451")
                course_field.send_keys("451")
            else:
                print("Course field not found")
            
            # Try to submit
            try:
                submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                print("Found submit button, clicking...")
                submit_button.click()
                time.sleep(5)
            except:
                print("Submit button not found")
                
        except Exception as e:
            print(f"Error during search: {e}")
        
        # Check page source for results
        page_source = driver.page_source
        print("Checking page source for results...")
        
        if "MATH 451" in page_source:
            print("Found MATH 451 in page source")
        if "Conner" in page_source:
            print("Found 'Conner' in page source")
        if "Winter 2026" in page_source:
            print("Found 'Winter 2026' in page source")
        
        # Try to find results table
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"Found {len(tables)} tables")
            
            for i, table in enumerate(tables):
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    print(f"Table {i}: {len(rows)} rows")
                    
                    if len(rows) > 2:  # Potential results table
                        for j, row in enumerate(rows):
                            if j < 2:  # Skip header rows
                                continue
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) > 5:
                                row_text = " ".join([cell.text for cell in cells])
                                if "451" in row_text:
                                    print(f"Row {j}: {row_text}")
                                    
                                    # Try to extract schedule info
                                    if len(cells) >= 8:
                                        try:
                                            instructor = cells[6].text.strip() if len(cells) > 6 else ""
                                            days = cells[8].text.strip() if len(cells) > 8 else ""
                                            class_time = cells[9].text.strip() if len(cells) > 9 else ""
                                            location = cells[11].text.strip() if len(cells) > 11 else ""
                                            
                                            if "Conner" in instructor:
                                                results.append({
                                                    "instructor": instructor,
                                                    "days": days,
                                                    "time": class_time,
                                                    "location": location
                                                })
                                                print(f"Found Conner's section: {days} {class_time} {location}")
                                        except Exception as e:
                                            print(f"Error extracting row data: {e}")
                except Exception as e:
                    print(f"Error processing table {i}: {e}")
                    
        except Exception as e:
            print(f"Error finding results: {e}")
        
        # If no results, try alternative approach
        if not results:
            print("No results found, trying alternative search...")
            # Try to find any MATH courses
            try:
                for table in tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) > 5:
                            row_text = " ".join([cell.text for cell in cells])
                            if "MATH" in row_text and "451" in row_text:
                                print(f"Found MATH 451 row: {row_text}")
                                # Extract what we can
                                if len(cells) >= 8:
                                    try:
                                        instructor = cells[6].text.strip() if len(cells) > 6 else ""
                                        days = cells[8].text.strip() if len(cells) > 8 else ""
                                        class_time = cells[9].text.strip() if len(cells) > 9 else ""
                                        location = cells[11].text.strip() if len(cells) > 11 else ""
                                        
                                        results.append({
                                            "instructor": instructor,
                                            "days": days,
                                            "time": class_time,
                                            "location": location
                                        })
                                        print(f"Found MATH 451 section: {instructor} {days} {class_time} {location}")
                                    except Exception as e:
                                        print(f"Error extracting data: {e}")
            except Exception as e:
                print(f"Error in alternative search: {e}")
    
    except Exception as e:
        print(f"Error during scraping: {str(e)}", file=sys.stderr)
    finally:
        driver.quit()
    
    return results

def main():
    """Main function"""
    print("Starting BYU class schedule scraper v0.3.0...")
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

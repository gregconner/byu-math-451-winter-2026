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
from selenium.webdriver.support.ui import Select

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
        # Use the specific URL with parameters
        driver.get("https://commtech.byu.edu/noauth/classSchedule/index.php?yearTerm=20133&creditType=2")
        
        print("Waiting for page to load...")
        time.sleep(5)
        
        # First, select Winter 2026 from the term dropdown
        print("Looking for term selector...")
        try:
            # Look for the term dropdown - it might be in a select element
            term_select = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='yearTerm'], select[id*='year'], select[id*='term']"))
            )
            print("Found term selector")
            
            # Create Select object and look for Winter 2026
            select = Select(term_select)
            winter_2026_found = False
            
            for option in select.options:
                if "Winter 2026" in option.text:
                    print(f"Found Winter 2026 option: {option.text}")
                    select.select_by_visible_text(option.text)
                    winter_2026_found = True
                    break
            
            if not winter_2026_found:
                print("Winter 2026 not found in dropdown, checking all options:")
                for option in select.options:
                    print(f"  - {option.text}")
                    
        except Exception as e:
            print(f"Error with term selector: {e}")
        
        # Wait for page to update after term selection
        if winter_2026_found:
            print("Waiting for page to update after term selection...")
            time.sleep(3)
        
        # Now look for the search fields - try a more comprehensive approach
        print("Looking for search fields...")
        
        # Get all input fields and examine them
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Found {len(inputs)} input fields")
        
        # Examine each input field to find the right ones
        dept_field = None
        catalog_field = None
        
        for i, input_field in enumerate(inputs):
            try:
                placeholder = input_field.get_attribute("placeholder")
                name = input_field.get_attribute("name")
                id_attr = input_field.get_attribute("id")
                type_attr = input_field.get_attribute("type")
                value = input_field.get_attribute("value")
                
                print(f"Input {i}: type={type_attr}, name={name}, id={id_attr}, placeholder={placeholder}, value={value}")
                
                # Look for department field
                if (placeholder and ("department" in placeholder.lower() or "dept" in placeholder.lower() or "subject" in placeholder.lower())) or \
                   (name and ("dept" in name.lower() or "subject" in name.lower())) or \
                   (id_attr and ("dept" in id_attr.lower() or "subject" in id_attr.lower())):
                    dept_field = input_field
                    print(f"  -> Identified as department field")
                
                # Look for catalog field
                if (placeholder and ("catalog" in placeholder.lower() or "course" in placeholder.lower() or "number" in placeholder.lower())) or \
                   (name and ("catalog" in name.lower() or "course" in name.lower() or "number" in name.lower())) or \
                   (id_attr and ("catalog" in id_attr.lower() or "course" in id_attr.lower() or "number" in id_attr.lower())):
                    catalog_field = input_field
                    print(f"  -> Identified as catalog field")
                    
            except Exception as e:
                print(f"Error examining input {i}: {e}")
        
        # If we still haven't found the fields, try looking for them by their position or context
        if not dept_field or not catalog_field:
            print("Trying alternative field identification...")
            
            # Look for fields near labels or in specific positions
            try:
                # Try to find fields by looking for labels or nearby text
                page_text = driver.page_source
                
                # Look for "Department" text and find nearby input
                if "Department" in page_text:
                    print("Found 'Department' text in page")
                    # Try to find input field that might be near this text
                    dept_candidates = driver.find_elements(By.XPATH, "//input[preceding::*[contains(text(), 'Department')]]")
                    if dept_candidates:
                        dept_field = dept_candidates[0]
                        print("Found department field by XPath")
                
                # Look for "Catalog Number" text and find nearby input
                if "Catalog Number" in page_text:
                    print("Found 'Catalog Number' text in page")
                    # Try to find input field that might be near this text
                    catalog_candidates = driver.find_elements(By.XPATH, "//input[preceding::*[contains(text(), 'Catalog')]]")
                    if catalog_candidates:
                        catalog_field = catalog_candidates[0]
                        print("Found catalog field by XPath")
                        
            except Exception as e:
                print(f"Error in alternative field identification: {e}")
        
        # Fill in the search fields
        if dept_field:
            print("Entering 'MATH' in department field")
            dept_field.clear()
            dept_field.send_keys("MATH")
        else:
            print("Department field not found")
        
        if catalog_field:
            print("Entering '451' in catalog field")
            catalog_field.clear()
            catalog_field.send_keys("451")
        else:
            print("Catalog field not found")
        
        # Look for and click the search button
        print("Looking for search button...")
        search_button = None
        try:
            # Try different selectors for the search button
            button_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "input[value*='Search']",
                "input[value*='search']",
                "button:contains('Search')",
                "input[value*='Submit']"
            ]
            
            for selector in button_selectors:
                try:
                    search_button = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"Found search button with selector: {selector}")
                    break
                except:
                    continue
            
            if not search_button:
                # Try to find by value text
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for input_field in inputs:
                    try:
                        value = input_field.get_attribute("value")
                        if value and ("search" in value.lower() or "submit" in value.lower()):
                            search_button = input_field
                            print(f"Found search button by value: {value}")
                            break
                    except:
                        continue
                        
        except Exception as e:
            print(f"Error finding search button: {e}")
        
        # Click the search button if found
        if search_button:
            print("Clicking search button...")
            search_button.click()
            time.sleep(5)
        else:
            print("Search button not found")
        
        # Check for results
        print("Checking for search results...")
        page_source = driver.page_source
        
        if "MATH 451" in page_source:
            print("Found MATH 451 in page source")
        if "Conner" in page_source:
            print("Found 'Conner' in page source")
        if "Winter 2026" in page_source:
            print("Found 'Winter 2026' in page source")
        
        # Look for results table
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
    print("Starting BYU class schedule scraper v0.5.0...")
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

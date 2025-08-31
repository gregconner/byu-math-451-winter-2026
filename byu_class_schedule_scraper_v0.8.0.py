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
        if "Winter 2026" in page source:
            print("Found 'Winter 2026' in page source")
        
        # Now let's properly extract the schedule data from the results
        print("Extracting schedule data from results...")
        
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"Found {len(tables)} tables")
            
            # Examine both tables carefully
            for table_idx, table in enumerate(tables):
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"\nExamining Table {table_idx}: {len(rows)} rows")
                
                # Look at the first few rows to understand the structure
                for row_idx in range(min(3, len(rows))):
                    row = rows[row_idx]
                    cells = row.find_elements(By.TAG_NAME, "td")
                    th_cells = row.find_elements(By.TAG_NAME, "th")
                    
                    if th_cells:
                        print(f"  Row {row_idx} (header): {[cell.text for cell in th_cells]}")
                    elif cells:
                        print(f"  Row {row_idx} (data): {[cell.text for cell in cells]}")
                
                # If this table has more than 2 rows and looks like a schedule table, examine it more closely
                if len(rows) > 2:
                    print(f"  Table {table_idx} has {len(rows)} rows - examining for schedule data...")
                    
                    # Look for header row
                    header_row = rows[0]
                    header_cells = header_row.find_elements(By.TAG_NAME, "th")
                    if not header_cells:
                        header_cells = header_row.find_elements(By.TAG_NAME, "td")
                    
                    if header_cells:
                        print(f"  Headers: {[cell.text for cell in header_cells]}")
                        
                        # Look for schedule-related headers
                        header_texts = [cell.text.lower() for cell in header_cells]
                        if any(keyword in ' '.join(header_texts) for keyword in ['section', 'instructor', 'days', 'time', 'location']):
                            print(f"  This looks like a schedule table!")
                            
                            # Process data rows
                            for row_idx in range(1, len(rows)):
                                row = rows[row_idx]
                                cells = row.find_elements(By.TAG_NAME, "td")
                                
                                if len(cells) > 5:
                                    row_text = " ".join([cell.text for cell in cells])
                                    print(f"    Row {row_idx}: {row_text}")
                                    
                                    # Look for MATH 451 rows
                                    if "451" in row_text and "MATH" in row_text:
                                        print(f"    Found MATH 451 row!")
                                        
                                        # Try to extract schedule info based on column positions
                                        try:
                                            # Based on typical BYU schedule table structure
                                            if len(cells) >= 12:
                                                section = cells[0].text.strip() if len(cells) > 0 else ""
                                                type_info = cells[1].text.strip() if len(cells) > 1 else ""
                                                mode = cells[2].text.strip() if len(cells) > 2 else ""
                                                instructor = cells[3].text.strip() if len(cells) > 3 else ""
                                                credits = cells[4].text.strip() if len(cells) > 4 else ""
                                                term = cells[5].text.strip() if len(cells) > 5 else ""
                                                days = cells[6].text.strip() if len(cells) > 6 else ""
                                                start_time = cells[7].text.strip() if len(cells) > 7 else ""
                                                end_time = cells[8].text.strip() if len(cells) > 8 else ""
                                                location = cells[9].text.strip() if len(cells) > 9 else ""
                                                available = cells[10].text.strip() if len(cells) > 10 else ""
                                                waitlist = cells[11].text.strip() if len(cells) > 11 else ""
                                                
                                                print(f"      Section: {section}")
                                                print(f"      Type: {type_info}")
                                                print(f"      Mode: {mode}")
                                                print(f"      Instructor: {instructor}")
                                                print(f"      Credits: {credits}")
                                                print(f"      Term: {term}")
                                                print(f"      Days: {days}")
                                                print(f"      Time: {start_time} - {end_time}")
                                                print(f"      Location: {location}")
                                                print(f"      Available: {available}")
                                                print(f"      Waitlist: {waitlist}")
                                                
                                                # If this is Conner's section, add it to results
                                                if "Conner" in instructor:
                                                    results.append({
                                                        "section": section,
                                                        "type": type_info,
                                                        "mode": mode,
                                                        "instructor": instructor,
                                                        "credits": credits,
                                                        "term": term,
                                                        "days": days,
                                                        "start_time": start_time,
                                                        "end_time": end_time,
                                                        "time": f"{start_time} - {end_time}",
                                                        "location": location,
                                                        "available": available,
                                                        "waitlist": waitlist
                                                    })
                                                    print(f"      Added Conner's section to results")
                                                
                                                # Also add any MATH 451 section for reference
                                                elif "MATH" in row_text and "451" in row_text:
                                                    results.append({
                                                        "section": section,
                                                        "type": type_info,
                                                        "mode": mode,
                                                        "instructor": instructor,
                                                        "credits": credits,
                                                        "term": term,
                                                        "days": days,
                                                        "start_time": start_time,
                                                        "end_time": end_time,
                                                        "time": f"{start_time} - {end_time}",
                                                        "location": location,
                                                        "available": available,
                                                        "waitlist": waitlist
                                                    })
                                                    print(f"      Added MATH 451 section to results")
                                                    
                                        except Exception as e:
                                            print(f"      Error extracting row data: {e}")
                                            
                                            # Try alternative extraction if the first method failed
                                            try:
                                                # Look for specific patterns in the row text
                                                if "Conner" in row_text:
                                                    # Extract what we can from the text
                                                    import re
                                                    
                                                    # Look for day patterns
                                                    day_match = re.search(r'([MTWThFS]+)', row_text)
                                                    days = day_match.group(1) if day_match else ""
                                                    
                                                    # Look for time patterns
                                                    time_match = re.search(r'([0-9:]+(?:\s*[AP]M)?)', row_text)
                                                    time_str = time_match.group(1) if time_match else ""
                                                    
                                                    # Look for location patterns (building codes)
                                                    location_match = re.search(r'([A-Z]{2,4}\s+[0-9]+)', row_text)
                                                    location = location_match.group(1) if location_match else ""
                                                    
                                                    results.append({
                                                        "section": "MATH 451",
                                                        "instructor": "Conner",
                                                        "days": days,
                                                        "time": time_str,
                                                        "location": location,
                                                        "extracted_from": "pattern_matching"
                                                    })
                                                    print(f"      Added Conner's section using pattern matching")
                                                    
                                            except Exception as e2:
                                                print(f"      Error in alternative extraction: {e2}")
                
                # Also check the smaller table (might be the results table)
                elif len(rows) <= 3:
                    print(f"  Table {table_idx} has {len(rows)} rows - might be results table...")
                    
                    for row_idx, row in enumerate(rows):
                        cells = row.find_elements(By.TAG_NAME, "td")
                        th_cells = row.find_elements(By.TAG_NAME, "th")
                        
                        if th_cells:
                            print(f"    Row {row_idx} (header): {[cell.text for cell in th_cells]}")
                        elif cells:
                            print(f"    Row {row_idx} (data): {[cell.text for cell in cells]}")
                            
                            # Check if this row contains MATH 451 info
                            row_text = " ".join([cell.text for cell in cells])
                            if "451" in row_text and "MATH" in row_text:
                                print(f"    Found MATH 451 info in small table!")
                                
                                # Try to extract what we can
                                if "Conner" in row_text:
                                    # Extract what we can from the text
                                    import re
                                    
                                    # Look for day patterns
                                    day_match = re.search(r'([MTWThFS]+)', row_text)
                                    days = day_match.group(1) if day_match else ""
                                    
                                    # Look for time patterns
                                    time_match = re.search(r'([0-9:]+(?:\s*[AP]M)?)', row_text)
                                    time_str = time_match.group(1) if time_match else ""
                                    
                                    # Look for location patterns (building codes)
                                    location_match = re.search(r'([A-Z]{2,4}\s+[0-9]+)', row_text)
                                    location = location_match.group(1) if location_match else ""
                                    
                                    results.append({
                                        "section": "MATH 451",
                                        "instructor": "Conner",
                                        "days": days,
                                        "time": time_str,
                                        "location": location,
                                        "extracted_from": "small_table_pattern_matching"
                                    })
                                    print(f"      Added Conner's section from small table")
                
        except Exception as e:
            print(f"Error processing results: {e}")
        
        # If we still don't have results, try a different approach
        if not results:
            print("No results extracted, trying alternative parsing...")
            try:
                # Look for any text containing schedule information
                page_text = driver.page_source
                
                # Search for patterns that might contain schedule info
                import re
                
                # Look for patterns like "MWF" or "TTh" followed by time
                day_patterns = re.findall(r'([MTWThFS]+)\s*([0-9:]+(?:\s*[AP]M)?)', page_text)
                if day_patterns:
                    print(f"Found day/time patterns: {day_patterns}")
                
                # Look for instructor names
                instructor_patterns = re.findall(r'([A-Z][a-z]+,\s*[A-Z][a-z]+)', page_text)
                if instructor_patterns:
                    print(f"Found instructor patterns: {instructor_patterns}")
                    
                # Look for MATH 451 specifically
                math451_patterns = re.findall(r'(MATH\s+451[^<]*)', page_text)
                if math451_patterns:
                    print(f"Found MATH 451 patterns: {math451_patterns}")
                
                # Look for Conner specifically
                conner_patterns = re.findall(r'(Conner[^<]*)', page_text)
                if conner_patterns:
                    print(f"Found Conner patterns: {conner_patterns}")
                    
                # Since we know Conner and MATH 451 are in the page source, let's try to find them together
                # Look for text that contains both "Conner" and schedule-like information
                conner_sections = re.findall(r'(Conner[^<]*?)(?:MTWTh|MWF|TTh|MTW|MW|TTh|MT|MW|T|M|W|F|S)[^<]*?([0-9:]+(?:\s*[AP]M)?)[^<]*?([A-Z]{2,4}\s+[0-9]+)', page_text, re.IGNORECASE | re.DOTALL)
                if conner_sections:
                    print(f"Found Conner schedule sections: {conner_sections}")
                    
                    for section in conner_sections:
                        instructor = section[0].strip()
                        time_str = section[1].strip()
                        location = section[2].strip()
                        
                        # Try to extract days from the context
                        days_match = re.search(r'(MTWTh|MWF|TTh|MTW|MW|TTh|MT|MW|T|M|W|F|S)', section[0] + section[1] + section[2])
                        days = days_match.group(1) if days_match else ""
                        
                        results.append({
                            "section": "MATH 451",
                            "instructor": instructor,
                            "days": days,
                            "time": time_str,
                            "location": location,
                            "extracted_from": "conner_pattern_matching"
                        })
                        print(f"Added Conner's section using advanced pattern matching")
                        
            except Exception as e:
                print(f"Error in alternative parsing: {e}")
    
    except Exception as e:
        print(f"Error during scraping: {str(e)}", file=sys.stderr)
    finally:
        driver.quit()
    
    return results

def main():
    """Main function"""
    print("Starting BYU class schedule scraper v0.8.0...")
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

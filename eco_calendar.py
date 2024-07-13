from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import time
import os
import sys

# Check if both arguments are provided
if len(sys.argv) != 3:
    print("Usage: python economic_calendar.py <start_date> <end_date>")
    print("Date format should be MM-DD-YYYY")
    sys.exit(1)

# Validate date format
def validate_date(date_string):
    try:
        datetime.strptime(date_string, '%m-%d-%Y')
        return True
    except ValueError:
        return False


start_date_key = sys.argv[1]
to_date_key = sys.argv[2]

if not (validate_date(start_date_key) and validate_date(to_date_key)):
    print("Invalid date format. Please use MM-DD-YYYY.")
    sys.exit(1)

# Setup WebDriver
driver = webdriver.Chrome()
driver.get("https://www.investing.com/economic-calendar/")

def get_scroll_height():
    return driver.execute_script("return document.body.scrollHeight")

try:
    # Scroll down by a certain number of pixels
    driver.execute_script("window.scrollTo(0, 200);")  # Adjust the number based on your needs

    # Optionally, wait a bit for the pop-up to be potentially triggered by scrolling
    driver.implicitly_wait(2)
    # Check if the pop-up is present and visible
    wait = WebDriverWait(driver, 5)
    close_button = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'largeBannerCloser')))
    
    # If the close button is visible, click it
    close_button.click()
    print("Pop-up closed.")
except TimeoutException:
    # If no pop-up is visible within 5 seconds, proceed
    print("No pop-up to close.")

# Wait for the page to load
WebDriverWait(driver, 5).until(
    EC.presence_of_element_located((By.ID, "datePickerToggleBtn"))
)

# Open date picker button
date_picker_toggle_btn = driver.find_element(By.ID, "datePickerToggleBtn")
date_picker_toggle_btn.click()
from_date = driver.find_element(By.ID, "startDate")
from_date.click()
for _ in range(10):  # Adjust the range based on the maximum expected input size
    from_date.send_keys(Keys.BACKSPACE)
from_date.send_keys(start_date_key)  # Enter new date
to_date = driver.find_element(By.ID, "endDate")
to_date.click()
for _ in range(10):
    to_date.send_keys(Keys.BACKSPACE)
to_date.send_keys(to_date_key)
time.sleep(3)

# Apply the date range
apply_button = driver.find_element(By.ID, "applyBtn")
apply_button.click()
time.sleep(3)

last_height = get_scroll_height()
while True:
    # Scroll down to the bottom of the page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    # Wait for the page to load
    time.sleep(3)  # Adjust sleep time as necessary

    # Calculate new scroll height and compare with last scroll height
    new_height = get_scroll_height()
    if new_height == last_height:
        # Break the loop if no more content is loaded
        print("Reached the bottom of the page.")
        break
    last_height = new_height

# Wait for the data to load
time.sleep(5)

page_source = driver.page_source

# Clean up
driver.quit()

soup = BeautifulSoup(page_source, "html.parser")
table = soup.find_all(class_ = "js-event-item")

result = []
base = {}

for bl in table:

    # Extract each event date and format it as '%d/%b/%Y'
    time = pd.to_datetime(bl['data-event-datetime']).strftime('%d/%b/%Y')
    # Extract the currency/country 
    currency = bl.find(class_ ="left flagCur noWrap").text.split(' ')[-1]
    # Extract the importance level from 'data-img_key' which are 'bull1', 'bull2', 'bull3'
    # Cleaned as INT (1,2,3)
    importance = int(bl.find(class_="left textNum sentiment noWrap").get('data-img_key', '')[-1])
    # Extract the event names
    event = bl.find(class_ ="left event").get_text(strip=True)

    # Extract the event id to match actual/forecast/previous
    event_id = bl['id'].split('_')[-1] 
    actual = bl.find(id={f"eventActual_{event_id}"})
    forecast = bl.find(id={f"eventForecast_{event_id}"})
    previous = bl.find(id=f"eventPrevious_{event_id}")
            
    # Extract text safely
    actual_text = actual.get_text(strip=True) if actual else 'NULL'
    forecast_text = forecast.get_text(strip=True) if forecast else 'NULL'
    previous_text = previous.get_text(strip=True) if previous else 'NULL'
    
    
    # Create a dictionary for the current event
    calendar = {
        'Date': time,
        'Currency': currency,
        'Importance': importance,
        'Event': event,
        'Actual': actual_text,
        'Forecast': forecast_text,
        'Previous': previous_text
    }
    # Append the dictionary to the result list
    result.append(calendar)

df = pd.DataFrame(result)
os.makedirs('data', exist_ok=True)
df.to_csv(f"data/{start_date_key}_{to_date_key}_economicEvents.csv", index=False)
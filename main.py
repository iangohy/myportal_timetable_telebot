from datetime import date
import os
import requests

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

from dotenv import load_dotenv
load_dotenv()

def get_screenshot(username, password, api_key, chat_id, next_week = 0):
    '''
    Get screenshot of timetable (for lessons up till 9pm)

    Arguments:
    username - MyPortal login (student ID)
    password - MyPortal password
    api_key - Telegram bot api_key
    chat_id - Chat to send screenshot to
    next_week - 0 for this week's timetable, 1 for this and next week's timetable

    Return:
    None
    '''

    print("-----SUTD Timetable-----")
    print("Starting webdriver...")
    firefox_options = Options()
    firefox_options.add_argument("-headless")
    gecko_path = os.getenv("gecko_path")
    if gecko_path is None:
        gecko_path = r'./geckodriver.exe'
    driver = webdriver.Firefox(options = firefox_options, executable_path=gecko_path)

    # Login
    driver.get("https://myportal.sutd.edu.sg/psp/EPPRD/EMPLOYEE/EMPL/")
    print("Logging-in...")

    # Check if login succeeded
    try:
        username_element = driver.find_element_by_id("userid") 
        username_element.send_keys(username)
        password_element = driver.find_element_by_id("pwd") 
        password_element.send_keys(password)
        password_element.send_keys(Keys.RETURN)
        WebDriverWait(driver, 10).until(
            EC.title_is("SUTD MyPortal")
        )
        print("Login successful")
    except Exception as e:
        print("Error occurred on sign-in")
        print(e)

        raise Exception("Unable to login!")


        
    # Get XML
    driver.get("https://sams.sutd.edu.sg/psc/CSPRD/EMPLOYEE/HRMS/c/SA_LEARNER_SERVICES.SSR_SSENRL_SCHD_W.GBL")

    try:
        WebDriverWait(driver, 5).until(
            EC.title_is("View My Weekly Schedule")
        )
    except:
        driver.close()
        raise Exception("Error getting weekly schedule")

    # Show class title, instructor and change end time
    title_checkbox = driver.find_element_by_id("DERIVED_CLASS_S_SSR_DISP_TITLE")
    title_checkbox.click()
    instructor_checkbox = driver.find_element_by_id("DERIVED_CLASS_S_SHOW_INSTR")
    instructor_checkbox.click()
    end_time = driver.find_element_by_id("DERIVED_CLASS_S_MEETING_TIME_END")
    end_time.clear()
    end_time.send_keys("21")
    refresh_cal = driver.find_element_by_id("DERIVED_CLASS_S_SSR_REFRESH_CAL$38$")
    refresh_cal.click()
    
    try:
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located((By.ID, "WAIT_win0"))
        )
    except:
        driver.close()
        raise Exception("Refresh calendar timeout")


    # Create screenshots folder if it does not exist 
    if not os.path.exists('screenshots'):
        os.makedirs('screenshots')

    filename = f"screenshots/{date.today().isoformat()}.png"
    table = driver.find_element_by_id("SSR_DUMMY_REC$scroll$0")
    table.screenshot(filename)
    print(f"{filename} saved")
    send_photo_telegram(api_key, chat_id, filename)

    if next_week:
        next_week_element = driver.find_element_by_id("DERIVED_CLASS_S_SSR_NEXT_WEEK")
        next_week_element.click()
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.ID, "WAIT_win0"))
            )
        except:
            driver.close()
            raise Exception("Refresh calendar timeout")
        filename_next = f"screenshots/{date.today().isoformat()}_nextweek.png"
        table_next = driver.find_element_by_id("SSR_DUMMY_REC$scroll$0")
        table_next.screenshot(filename_next)
        print(f"{filename_next} saved")
        send_photo_telegram(api_key, chat_id, filename_next, 1)

    driver.close()
    return

def send_photo_telegram(api_key, chat_id, filename, next_week = 0):
    url = f"https://api.telegram.org/bot{api_key}/sendPhoto"
    files = {'photo': open(filename, 'rb')}

    if next_week:
        data = {'chat_id' : chat_id, 'caption' : 'Next Week'}
    else:
        data = {'chat_id' : chat_id, 'caption' : 'This Week'}

    r = requests.post(url, files=files, data=data)
    if r.status_code == 200:
        print("Send to telegram success")
    else:
        print("Send to telegram failed")
    return

def send_msg_telegram(api_key, chat_id, text):
    '''
    Sends HTML parsed message to telegram chat
    '''
    requests.get(f"https://api.telegram.org/bot{api_key}/sendMessage?chat_id={chat_id}&parse_mode=HTML&text={text}")


if __name__ == "__main__":
    get_screenshot(os.getenv("myportal_user"), os.getenv("myportal_pw"), os.getenv("api_key"), os.getenv("chat_id"), os.getenv("next_week"))
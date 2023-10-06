from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import settings

# TODO: Add logging


def main():
    # AM Storage Service credentials
    username = settings.am_ss_user['username']
    password = settings.am_ss_user['password']

    options = Options()  # get Chrome options
    options.add_argument('--headless=new')  # set headless mode
    driver = webdriver.Chrome(options=options)  # initialize Chrome driver

    driver.get(settings.am_ss_login)  # navigate to login page
    driver.find_element(By.ID, 'id_username').send_keys(username)  # find username field and insert username
    driver.find_element(By.ID, 'id_password').send_keys(password)  # find password field and insert password
    driver.find_element(By.XPATH, '/html/body/div[2]/div/form/input[2]').click()  # find login button and click

    # wait the ready state to be complete
    WebDriverWait(driver=driver, timeout=10).until(
        lambda x: x.execute_script('return document.readyState === "complete"')
    )

    error_message = 'Your username and password didn\'t match. Please try again.'  # error message to look for
    errors = driver.find_elements(By.XPATH, '/html/body/div[2]/div/p')  # find all error messages

    # print the errors optionally
    # for e in errors:
    #     print(e.text)

    # if we find that error message within errors, then login is failed
    if any(error_message in e.text for e in errors):
        print('[!] Login failed')
    else:
        print('[+] Login successful')

    print(driver.current_url)

    # TODO: Delete packages

    driver.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import settings
import sys

# TODO: Add logging


def main():
    reason_text = sys.argv[1]  # get the reason text from the command line

    # AM Storage Service credentials
    username = settings.am_ss_user['username']
    password = settings.am_ss_user['password']

    options = Options()  # get Chrome options
    options.add_argument('--headless=new')  # set headless mode
    driver = webdriver.Chrome(options=options)  # initialize Chrome driver

    driver.get(settings.am_ss_url + 'login')  # navigate to login page
    driver.find_element(By.ID, 'id_username').send_keys(username)  # find username field and insert username
    driver.find_element(By.ID, 'id_password').send_keys(password)  # find password field and insert password
    driver.find_element(By.XPATH, '/html/body/div[2]/div/form/input[2]').click()  # find login button and click

    # wait the ready state to be complete
    WebDriverWait(driver=driver, timeout=10).until(
        lambda x: x.execute_script('return document.readyState === "complete"')
    )

    error_message = 'Your username and password didn\'t match. Please try again.'  # error message to look for
    errors = driver.find_elements(By.XPATH, '/html/body/div[2]/div/p')  # find all error messages

    # if we find that error message within errors, then login is failed
    if any(error_message in e.text for e in errors):
        print('[!] Login failed')
    else:
        print('[+] Login successful')

    # xpaths to elements in first row of table
    file = '/html/body/div[2]/div/div[1]/table/tbody/tr[1]/td[1]'  # file name
    reason = '/html/body/div[2]/div/div[1]/table/tbody/tr[1]/td[7]/form/p/textarea'  # reason field
    approve = '/html/body/div[2]/div/div[1]/table/tbody/tr[1]/td[7]/form/input[2]'  # approve button

    packages_to_delete = True  # flag to keep the loop going

    # while there are packages to delete
    while packages_to_delete is True:
        driver.get(settings.am_ss_url + 'packages/package_delete_request/')  # navigate to package delete request page
        try:
            aip = driver.find_element(By.XPATH, file).text  # get the file name
            driver.find_element(By.XPATH, reason).send_keys(reason_text)  # find reason field and insert reason text
            driver.find_element(By.XPATH, approve).click()  # find approve button and click
        except Exception:  # if we can't find the elements, then there are no packages to delete
            print('No packages to delete')
            packages_to_delete = False  # set the flag to false to break the loop
            continue  # continue to the next iteration of the loop
        print('Package deleted: {}'.format(aip))  # print the name of the package that was deleted

    driver.close()


if __name__ == '__main__':
    main()

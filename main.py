from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from logging.handlers import TimedRotatingFileHandler
import settings
import sys
import logging

# AIP Deletion log
logdir = settings.log_dir  # set the log directory
log_file = logdir + '/aip_delete.log'  # set the log file
aip_log = logging.getLogger('aip_delete')  # create the scheduler log
aip_log.setLevel(logging.INFO)  # set the scheduler log level
file_handler = TimedRotatingFileHandler(log_file, when='midnight')  # create a file handler
file_handler.setLevel(logging.INFO)  # set the file handler level
file_handler.setFormatter(  # set the file handler format
    logging.Formatter(
        '%(asctime)s %(levelname)-8s %(message)s', datefmt='%m/%d/%Y %H:%M:%S'
    ))
aip_log.addHandler(file_handler)  # add the file handler to the scheduler log


def main():
    count = 0  # initialize count
    aip_log.info('Starting AIP Deletion')  # log that the script is starting

    # Check if reason text is provided
    try:
        reason_text = sys.argv[1]  # get the reason text from the command line
    except IndexError:  # if no reason text is provided, then exit
        aip_log.error('Aborting. No reason provided for deleting AIPs')  # log that no reason was provided
        sys.exit(1)  # exit the script

    # AM Storage Service credentials
    username = settings.am_ss_user['username']
    password = settings.am_ss_user['password']

    # Set up Chrome driver
    options = Options()  # get Chrome options
    options.add_argument('--headless=new')  # set headless mode
    driver = webdriver.Chrome(options=options)  # initialize Chrome driver

    # Login to AM Storage Service
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

    if any(error_message in e.text for e in errors):  # if we find that error message, then login is failed
        aip_log.error('Aborting. AM Storage Service login failed')  # log that login failed
        sys.exit(1)  # exit the script
    else:  # otherwise, login is successful
        aip_log.info('AM Storage Service login successful')  # log that login was successful

    # xpaths to elements in first row of table
    file = '/html/body/div[2]/div/div[1]/table/tbody/tr[1]/td[1]'  # file name cell
    old_aip = ''  # old file
    reason_field = '/html/body/div[2]/div/div[1]/table/tbody/tr[1]/td[7]/form/p/textarea'  # reason field
    approve_button = '/html/body/div[2]/div/div[1]/table/tbody/tr[1]/td[7]/form/input[2]'  # approve button

    packages_to_delete = True  # flag to keep the loop going

    # while there are packages to delete
    while packages_to_delete is True:

        driver.get(settings.am_ss_url + 'packages/package_delete_request/')  # navigate to package delete request page

        # wait the ready state to be complete
        WebDriverWait(driver=driver, timeout=10).until(
            lambda x: x.execute_script('return document.readyState === "complete"')
        )

        if check_if_element_exists(driver, reason_field) is True \
                and check_if_element_exists(driver, approve_button) is True:
            aip = driver.find_element(By.XPATH, file).text  # get the file name
            reason = driver.find_element(By.XPATH, reason_field)  # get the reason text
            approve = driver.find_element(By.XPATH, approve_button)  # get the approve button text
            reason.send_keys(reason_text)  # find field and insert text
            approve.click()  # find approve button and click
            aip_log.info('Deleting {}'.format(aip))  # log that the package was deleted
            count += 1  # increment count
            continue  # continue to the next iteration of the loop

        else:  # if reason field and approve button missing, no packages to delete
            aip_log.warning('No packages to delete')  # log that there are no packages to delete
            packages_to_delete = False  # set the flag to false to break the loop
            continue  # continue to the next iteration of the loop

    driver.close()  # close the browser
    aip_log.info('Deleted {} package(s)'.format(count))  # log the number of packages that were deleted
    aip_log.info('AIP Deletion Complete')  # log that the script is complete


def check_if_element_exists(driver, xpath):
    try:
        driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True


if __name__ == '__main__':
    main()

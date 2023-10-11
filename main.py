from selenium import webdriver
from selenium.common import NoSuchElementException, WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from logging.handlers import TimedRotatingFileHandler
import settings
import sys
import logging

# AIP Deletion log
logdir = settings.log_dir  # set the log directory
log_file = './log/aip_delete.log'  # set the log file
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
    reason_text = 'approve-aip-deletion batch script'  # initialize reason text

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
    file = '//*[@id="DataTables_Table_0"]/tbody/tr[1]/td[contains(@class, "sorting_1")]'
    reason_field = '//*[@id="DataTables_Table_0"]/tbody/tr[1]/td[7]/form/p/textarea[contains(@id, "status_reason")]'
    approve_button = '//*[@id="DataTables_Table_0"]/tbody/tr[1]/td[7]/form/input[@name="approve"]'

    packages_to_delete = True  # flag to keep the deletion loop going

    # Go to package delete request page
    try:
        driver.get(settings.am_ss_url + 'packages/package_delete_request/')  # load page
    except WebDriverException as e:  # if can't load page, abort
        aip_log.error('Unable to load Package Delete Requests. Aborting. {}'.format(e))  # log the error
        sys.exit(1)  # exit the script

    # wait for the DOM to load
    WebDriverWait(driver=driver, timeout=60).until(
        lambda x: x.execute_script('return document.readyState === "complete"')
    )

    # while there are packages to delete
    while packages_to_delete is True:

        # Check whether first row of table contains reason field and approve button
        if check_if_element_exists(driver, reason_field) is True \
                and check_if_element_exists(driver, approve_button) is True:

            # Delete the package in the first row
            aip = driver.find_element(By.XPATH, file).text  # get the file name
            driver.find_element(By.XPATH, reason_field).send_keys(reason_text)  # find reason field and insert text
            driver.find_element(By.XPATH, approve_button).click()  # find approve button and click

            # Wait for package file to appear in first row
            try:
                WebDriverWait(driver=driver, timeout=60).until(
                    EC.presence_of_element_located((By.XPATH, file))
                )
            except TimeoutException:  # if page load times out, abort
                aip_log.warning('Page load timed out. Aborting.')  # log the error
                packages_to_delete = False  # set flag to false to exit loop
                continue  # continue to next iteration of loop

            # look for success message in alert
            success_message = 'Request approved: Package deleted successfully.'  # success message to look for
            alert = driver.find_element(  # get the alert text
                By.XPATH,
                '/html/body/div[2]/div/div[contains(@class, "alert")]'
            ).text

            if success_message in alert:  # if we find that success message, then delete was successful
                aip_log.info('Deleted {}'.format(aip))  # log that the package was deleted
                count += 1  # increment count
                continue  # continue to next iteration of loop
            else:  # otherwise, delete was not successful
                aip_log.error('Failed to delete {}'.format(aip))
                continue  # continue to next iteration of loop

        else:  # if reason field and approve button missing, no packages to delete
            print('No packages to delete')  # log that there are no packages to delete
            packages_to_delete = False  # set flag to false to exit loop
            continue  # continue to next iteration of loop

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

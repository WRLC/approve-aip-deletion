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
    reason = '/html/body/div[2]/div/div[1]/table/tbody/tr[1]/td[7]/form/p/textarea'  # reason field
    approve = '/html/body/div[2]/div/div[1]/table/tbody/tr[1]/td[7]/form/input[2]'  # approve button

    packages_to_delete = True  # flag to keep the loop going

    # while there are packages to delete
    while packages_to_delete is True:
        driver.get(settings.am_ss_url + 'packages/package_delete_request/')  # navigate to package delete request page

        try:  # try to find the file name cell
            aip = driver.find_element(By.XPATH, file).text  # get the file name

            if aip != old_aip:  # make sure file name is different from the last one
                if old_aip != '':  # if this is not the first iteration of the loop
                    count += 1  # increment the count
                    aip_log.info('Package deleted: {}'.format(old_aip))  # log the name of the package that was deleted

                try:  # try to delete the package
                    driver.find_element(By.XPATH, reason).send_keys(reason_text)  # find reason field and insert text
                    driver.find_element(By.XPATH, approve).click()  # find approve button and click

                except NoSuchElementException:  # if we can't find the elements, then there are no packages to delete
                    aip_log.warning('No packages to delete')  # log that there are no packages to delete
                    packages_to_delete = False  # set the flag to false to break the loop
                    continue  # continue to the next iteration of the loop

                aip_log.info('Found package to delete')  # log the name of the package to delete
                old_aip = aip  # save the old file name

            else:  # if the file name is the same as the last one, then deletion failed
                aip_log.error('Failed to delete package: {}'.format(aip))  # log the package that failed to delete
                packages_to_delete = False  # set the flag to false to break the loop
                continue  # continue to the next iteration of the loop

        except NoSuchElementException:  # if we can't find the file name cell, then there are no packages to delete
            aip_log.warning('No packages to delete')  # log that there are no packages to delete
            packages_to_delete = False  # set the flag to false to break the loop
            continue  # continue to the next iteration of the loop

    driver.close()  # close the browser
    aip_log.info('Deleted {} package(s)'.format(count))  # log the number of packages that were deleted
    aip_log.info('AIP Deletion Complete')  # log that the script is complete


if __name__ == '__main__':
    main()

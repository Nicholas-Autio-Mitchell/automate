from urllib.request import urlopen
from time import strftime, sleep
from os.path import join, exists, getsize
from numpy.random import choice
from datetime import datetime, timedelta
from linecache import getline, clearcache
import logging as L

# Use this in order to check if there is an internet connection
try:
    import httplib
except Exception:
    import http.client as httplib

# set the working directory (log files will be written there)
WORKINGDIR = '/home/n1k31t4/Dropbox/'
addr_book = 'ip.txt'
logfile = 'ip.log'
OUT_FILE = join(WORKINGDIR, addr_book)
log_file_destination = join(WORKINGDIR, logfile)

# create address book file if it doesn't exist
if not exists(OUT_FILE):
    print('Creating new address book file: {} ...'.format(OUT_FILE))
    open(OUT_FILE, 'x').close()
    print('Success!')

# create log file if it doesn't exist
if not exists(log_file_destination):
    print('Creating new log file: {} ...'.format(log_file_destination))
    open(log_file_destination, 'x').close()
    print('Success!')

# configure the logger
L.basicConfig(
    filename=log_file_destination,
    level=L.INFO,
    format='%(asctime)s - %(levelname)s (Line: %(lineno)d) - %(message)s',
    datefmt='%d-%m-%Y %H:%M')

## ================================================ ##
##  functions to ensure smooth running of cron job  ##
## ================================================ ##


def have_internet():
    """Return True if there is an internet connection, otherwise False"""

    for timeout in [1, 5, 10, 20]:

        conn = httplib.HTTPConnection("www.google.com", timeout=timeout)

        try:
            conn.request("HEAD", "/")
            conn.close()
            L.info('\tA working internet connection was confirmed.')
            return True
        except Exception:
            conn.close()

        # return False if we haven't had a connection after trying all timeout
        # lengths
        return False


def validate_ip(website, ip_address):

    if '.' in ip_address:
        parts = ip_address.split('.')    # expect four parts for IPv4

        if len(parts) != 4:
            L.error('{} returned an IP address with {} parts, but 4 expected!'.format(
                website, len(ip_address)))
            return False

        for part in parts:
            if 0 <= int(part) <= 255:
                pass
            else:
                print(part)
                L.error('The IP address part {} lies outside of 0-255.'.format(int(part)))
                return False

    else:
        return False

    return True


# A list of websites that each return the current IPv4 address
websites = [
    'https://ipinfo.io/ip',
    'http://ipecho.net/plain'
    #'http://icanhazip.com/',     # returns the IPv6 address
    #'https://api.ipify.org/',    # requires an SSL certificate
    #'http://ident.me',           # returns the IPv6 address
]

## =================================================== ##
##  Some helper functions to write the IP as required  ##
## =================================================== ##


def last_known(fpath):
    """returns the last recorded IP address and the date-time it was collected
    """

    with open(fpath, 'r') as f:
        nlines = sum(1 for line in f)

    # ensure each execution recollects the line anew
    clearcache()
    # remove the trailing newline character
    last_ip = getline(fpath, nlines - 1)[:-1]
    when = getline(fpath, nlines)[16:32]

    return last_ip, when


def compare_ips(new_ip, last_recorded):
    """Return True if the last recorded in the file is the same as the newest obtained"""
    if new_ip == last_recorded:
        return True
    else:
        return False


def write_as_necessary(new_ip, address_book, time, website):
    """If the newly obtained IP address is different to the last recorded, append the new one to the list
    Return True if a new IP address is appended.
    Return False if the new address matches the old address.
    Return the time the last recorded IP address was recorded.
    """

    old_ip, when = last_known(address_book)
    SAME = compare_ips(new_ip, old_ip)

    if SAME:
        return False, when
    else:
        with open(address_book, 'a') as f:
            f.write(new_ip + '\n')
            f.write('Collected IP at {} using {}\n'.format(time, website))
        return True, when


## =================== ##
##  The main function  ##
## =================== ##


def get_ip():

    global SUCCESS

    # only try a certain number of times
    counter = 10

    while not SUCCESS and counter > 0:

        # select a website at random from those available
        website = websites[int(choice(len(websites), 1, replace=False))]

        # get the current time
        t = strftime('%Y-%m-%d %H:%M')

        # try to get the IP address
        try:
            ip = urlopen(website).read().decode('utf-8').strip()

        # Log any errors
        except Exception as e:
            # make the conscious decision here NOT to write a message into the address book.
            # this would break the function to connect to remote host, even if the last known is correct!
            # if the connection is failing, the user should always consult the
            # log file.

            # with open(OUT_FILE, 'a+') as f:
            #     f.write(
            #         '\n** Failed to open a {} at {}. See Log file for more information\n\n'.format(website, t))

            L.error("Couldn't open {}".format(website))
            L.info('\tFull exception: {}'.format(e))

            counter -= 1
            SUCCESS = False

        # perform checks on the obtained IP address
        try:
            is_valid = validate_ip(website, ip)
            assert is_valid, 'The obtained IP address is not a valid one!'

            if is_valid:
                WRITTEN, when = write_as_necessary(new_ip=ip, address_book=OUT_FILE, time=t, website=website)

                if WRITTEN:
                    L.info('\tNew IP address: {} - replaces old address from {}'.format(ip, when))
                else:
                    L.info('\tThe newly obtained IP address matches the last known, obtained at {}.'.format(
                        when))

                # with open(OUT_FILE, 'a+') as f:
                #     f.write(ip + '\n')
                #     f.write('Collected IP at {} using {}\n'.format(t, website))
                #L.info('\tSuccessfully collected IP address: {}'.format(ip))

            SUCCESS = True

        except AssertionError:
            with open(OUT_FILE, 'a+') as f:
                f.write('An AssertionError was thrown at: {}\n'.format(t))
                f.write('Check ip.log for more information\n')

            L.warning('The IP address obtained was not a correct IPv4 address!')
            L.info('\tThe returned IP address was: {}'.format(ip))

            counter -= 1
            SUCCESS = False

        # also write a notification into the
        finally:
            if not SUCCESS:
                with open(OUT_FILE, 'a') as f:
                    L.info('\tAttempting to use {} failed!'.format(website))

    return None


## ======================= ##
##  Run the main function  ##
## ======================= ##
# script is only called as main anyway

# Keep track of our attempt to get the IP address
SUCCESS = False

# Set a flag for a working internet connection
INTERNET = have_internet()

# get the IP address if internet connection exists
if INTERNET:
    get_ip()

# check for internet connection at intervals & reattempt
elif not INTERNET:

    for pause in [10, 20, 60]:
        sleep(pause)
        INTERNET = have_internet()

        if INTERNET:
            get_ip()
            break

# write an error message to the log file
else:
    L.error('Unable to confirm an internet connection!')

# Could think about restarting the wifi of the system at this point...
# would likely need to use Popen to send 'sudo systemctl restart NetworkManager'

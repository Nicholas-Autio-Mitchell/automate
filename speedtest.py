# ! /home/n1k31t4/anaconda3/envs/speedtest/bin/python

## ================================================================= ##
##  Read in the max download and upload speeds recorded and ... act  ##
## ================================================================= ##

import sys
import twitter
from subprocess import Popen, PIPE, check_output
from time import sleep, strftime
import urllib.request
import json

# -------------------- #
#  Configure a logger  #
# -------------------- #

from os.path import join, exists
import logging as L

# set the working directory (log files will be written there)
WORKINGDIR = '/home/n1k31t4/Dropbox/automate/'
logfile = 'speedtest.log'
log_file_destination = join(WORKINGDIR, logfile)

# create log file if it doesn't exist
if not exists(log_file_destination):
    print('Creating new log file: {} ...'.format(log_file_destination))
    open(log_file_destination, 'x').close()
    print('Created new log file: {}'.format(logfile))

# logging options - by default only minute resolution provided
L.basicConfig(
    filename=log_file_destination,
    level=L.INFO,
    format='%(asctime)s - %(levelname)s (Line: %(lineno)d) - %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S')

# ----------------------------------------------------------------------------- #
#  Provide this file with access to the environment packages in env: speedtest  #
# ----------------------------------------------------------------------------- #

sys.path.insert(0, '/home/n1k31t4/anaconda3/envs/speedtest/lib/python3.5/site-packages/')

# -------------------------- #
#  Log into the Twitter API  #
# -------------------------- #

api = twitter.Api(
    consumer_key        ='TPiQWlvALqR9vGG0D32g7fu5b',
    consumer_secret     ='8i3KgfE3JjwXO80oqJETOLTq35kY0S64sA71M',
    access_token_key    ='911083648572269027-3NVFhN1An5l',
    access_token_secret ='pfEk2yjMYMSMhn4BG3QsYIfkZDwpfEk2yjMYMSMhn4')

# print(api.VerifyCredentials())


def get_info(speedtest_output, input_type='dict', verbose=True):
    """Parse the output of speedtest-cli to get the upload and download speeds.
    Additionally, the link to the related image is returned"""

    # dictionary in which to store results
    output = {}

    if input_type == 'dict':
        output['up'] = speedtest_output['upload'] / 10**6
        output['down'] = speedtest_output['download'] / 10**6
        output['imlink'] = speedtest_output['share']
        return output

    elif input_type == 'text':
        words = speedtest_output.split(' ')
        for i, word in enumerate(words):
            if 'Download:' in word:
                output['down'] = words[i + 1]
            elif 'Upload:' in word:
                output['up'] = words[i + 1]
            elif 'results:' in word:
                output['link'] = words[i + 1]
            else:
                pass

        if verbose:
            print(words)

        return output


# ----------------------------------------- #
#  Run the speedtest via terminal commands  #
# ----------------------------------------- #

# output file
f = join(WORKINGDIR, 'output.json')

# execute the command to test the internet speed:
_ = check_output('speedtest-cli --share --json > {}'.format(f), shell=True)
# the results of 'speedtest-cli' are returned in Mb/s
with open(f, 'r') as fh:
    content = json.load(fh)

# # another way of running the command:
# proc = Popen('speedtest-cli --json --share > {}'.format(f), stdout=PIPE, shell=True)
# proc.wait()
# # get the output
# stdout = proc.communicate()[0]
# print(str(stdout))

# ----------------------------------- #
#  If conditions are met, send tweet  #
# ----------------------------------- #

# get the upload and download speeds
output = get_info(content, verbose=True)

# set acceptable limit
MIN = 35
print('Download speed was {:.2f}'.format(output['down']))

if output['down'] < MIN:

    L.warning('Internet speeds were: Up = {0:.1f}, Down = {1:.1f}'.format(output['up'], output['down']))
    print('Speed less that minimum: {} - measured: {}'.format(MIN, output['down']))
    # create the tweet text to be sent
    tweet_en = '@MNet - why is my internet so slow? Up: {0:.1f} Mbps - Down {1:.1f} Mbps. I pay 30€/month for 100 Mbps! '.format(
        output['up'], output['down'])
    tweet_de = '@MNet - warum ist mein Internet so langsam? Up: {0:.1f} Mbps - Down {1:.1f} Mbps. Ich zahle 30€/Monat für 100 Mbps!'.format(
        output['up'], output['down'])

    imfile = join(WORKINGDIR, 'latest_speed.png')

    try:
        # get the image to be posted
        urllib.request.urlretrieve(content['share'], imfile)

        # ---------------------------- #
        #  Send the tweets with image  #
        # ---------------------------- #

        # send the tweet with an image of the speedtest result
        _ = api.PostMedia(tweet_de, imfile)
        sleep(5)
        _ = api.PostMedia(tweet_en, imfile)

        L.info('Low speeds measured - tweet sent with image')

    except Exception as e:    # don't know which errors might arise
        L.warning('Low speeds measured, and speedtest image could not be obtained')
        # assuming the image download failed, just post the text
        _ = api.PostMedia(tweet_de)
        sleep(5)
        _ = api.PostMedia(tweet_en)

else:
    L.info('Internet speeds were: Up = {0:.1f}, Down = {1:.1f}'.format(output['up'], output['down']))

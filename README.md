# automate
Scripts used locally to run mundane tasks or perform checks regularly using tools like [`cron`](https://en.wikipedia.org/wiki/Cron).


## Speed test

------

Checks the internet connection speed and if below a certain threshold, will send a tweet to e.g. the internet provider along with the image containing the speed test results. Can make this run on a Raspberry Pi quite easily.

This requires two non-standard package installations:

1. `pip install twitter` - [homepage](http://python-twitter.readthedocs.io/en/latest/index.html)
2. `pip install speedtest-cli` - [homepage](https://github.com/sivel/speedtest-cli)

#### Example image in tweet: 
![alt text](./latest_speed.png)



## Push IP

------

This is required because modern (public) IP4 addresses are dynamic - changing roughly once per day.
Attains the local public IP address of a machine and writes it to a log file in a dynamically synchronised folder (e.g. Dropbox, Google Drive), from where it can be read and used for remote ssh connection.



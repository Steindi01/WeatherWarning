WeatherWarning
==============

Python program tweets current weather warnings from ZAMG (www.zamg.ac.at).

Before using this program it is necessary to install python-twitter package for python. You will find the resources for this package at: https://github.com/bear/python-twitter

Use the program by simply running it from the command line with the following command:
  python Weatherwarning.py <check interval> <path to user credentials>
  
  check interval: This argument defines how often the program checks for new weather warnung from ZAMG.
  path to user credentials: It is necessary to generate an API-key at https://dev.twitter.com/. Afterwards save the credentials in one file and use the following schema: Use only the first line. Seperate the values by a space character. Use this order: <consumer_key> <consumer_secret> <access_token_key> <access_token_secret>. The path to this document must be used as second argument.
  

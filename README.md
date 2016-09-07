# Python

This is a simple slack bot I coded for work.

It will take the staff roster which is already posted in HTML on a web page.

It will then format the roster data, add it as an attachment and post it as a message to the desired slack channel.

It will do this using a cron job set to repeat for specific dates/times.

This program makes use of the following libraries:
SlackClient - A light python wrapper around the offical Slack API
Requests - To pull the roster data from the web page.
APScheduler - To schedule the jobs to post as specific times/dates.
RE - Python Regular Expressions library, for parsing and formatting the data.
Flask - A python MVC web micro-framework. I only use it here in it's simplest form to keep a running background process to keep the thread alive for the scheduler.

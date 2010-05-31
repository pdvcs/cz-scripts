#!/usr/bin/python

import os
import random

print "Content-Type: text/html"
print "Expires: now\n"

print """<html>
<head>
<title>Request Headers</title>
<style type="text/css">
  body, td { font-family: Calibri, Geneva, Verdana, sans-serif; }
  table, td { border-collapse: collapse; border: 1px solid black; padding: 5px;}
</style>
</head>
<body>
<table>
"""
v = ('REMOTE_ADDR',
    'HTTP_ACCEPT',
    'HTTP_USER_AGENT',
    'HTTP_VIA',
    'HTTP_X_FORWARDED_FOR',
    'HTTP_CLIENT_IP',
    'HTTP_REFERER',
    'SERVER_PROTOCOL')

for i in v:
    try:
        s = os.environ[i]
    except KeyError:
        if i == 'HTTP_REFERER':
            s = '(No Referer)'
        else:
            s = '&nbsp;'
    print '<tr><td bgcolor="#dddddd"><b>', i, '</b></td><td>', s, '</td></tr>'

print '\n</table><p><a href="http://www.chaoszone.org/dyn/env.py?cb=%d">Reload this page &raquo;</a></p>' % (random.randrange(101, 9999))
print '</body></html>\n'

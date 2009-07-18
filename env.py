#!/usr/bin/python

# See LICENSE.txt in this source repository for terms of use.
# Displays HTTP header information sent by the browser.

import os
import random

print "Content-Type: text/html"
print "Expires: now\n"

print "<HTML><HEAD><TITLE>Request Headers</TITLE></HEAD><BODY>\n";
print "<TABLE BORDER=1>\n";

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
            s = '--No Referer Information Present.--'
        else:
            s = '&nbsp;'
    print '<TR><TD BGCOLOR=#CCCCCC>', i, '</TD><TD>', s, '</TD></TR>'

print '\n</TABLE><P><A HREF="http://www.chaoszone.org/dyn/env.py?cb=%d">Reload this page &raquo;</A></P>' % (random.randrange(101, 9999))
print '</BODY></HTML>\n'

#!/usr/bin/python

# See LICENSE.txt in this source repository for terms of use.
# Generates an RSS feed (with images) for the Archie Daily Comics at
# http://www.archiecomics.com/pops_shop/dailycomics/dailycomic.html

# TODO: update, the display logic appears to have changed.

# image url: http://www.archiecomics.com/pops_shop/dailycomics/image07.gif

from time import time, gmtime, strftime

def GetImageData ():
    imgnums = []
    todaysDate = gmtime(time())[2] # the date of month, like 19 or 27
    for ix in range(todaysDate, todaysDate-7, -1): # last 7 days
        if ix < 1:
            break
        imgnums.append(ix)
    return imgnums

def RssHeader ():
    print """<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0">
    <channel>
    <title>Archie Daily Comic</title>
    <link>http://www.archiecomics.com/pops_shop/dailycomics/dailycomic.html</link>
    <description>Today's Newspaper Strip</description>
    """

def RssBody (imginfo):
    timeNow = gmtime(time())
    vtimeNow = []
    for tmp in timeNow: vtimeNow.append(tmp)
   
    for imgnum in imginfo:
        vtimeNow[2] = imgnum
        pubDate = strftime("%a, %d %b %Y 00:00:00 UTC", vtimeNow)
        print """
            <item>
            <title>Issue %(num)d</title>
            <description><![CDATA[ <img src="http://www.archiecomics.com/pops_shop/dailycomics/image%(num)02d.gif" alt="Archie" /> ]]></description>
            <link>http://www.archiecomics.com/pops_shop/dailycomics/dailycomic.html</link>
            <guid isPermaLink="false">www.archiecomics.com:dailycomics:archie:%(year)d%(month)02d%(num)02d</guid>
            <pubDate>%(pubdate)s</pubDate>
            </item>""" % { 'num': imgnum, 'year': timeNow[0], \
                           'month': timeNow[1], 'pubdate': pubDate }

def RssFooter ():
    print "</channel></rss>"

def ExpiryTime ():
    # content expires 12 hours from now
    return strftime("%a, %d %b %Y %H:%M:%S UTC", gmtime(time() + 43200))

def Main ():
    print "Content-Type: application/rss+xml"
    print "Expires: " + ExpiryTime() + "\n"
    RssHeader()
    RssBody(GetImageData())
    RssFooter()

if __name__ == '__main__':
    Main()

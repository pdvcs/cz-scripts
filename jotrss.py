#!/usr/bin/python

# See LICENSE.txt in this source repository for terms of use.
# Synthesizes an RSS feed with images for the Joy of Tech comic strip.
# http://www.geekculture.com/joyoftech/

# permalink: http://www.geekculture.com/joyoftech/joyarchives/711b.html
# image url: http://www.geekculture.com/joyoftech/joyimages/711b.???

import urllib, re
from xml.dom import minidom
from time import time, gmtime, strftime

IMGDB = 'jotrss-imgdb.txt'

def GetImageFilenameFromPage (url):
    opener = urllib.urlopen(url)
    content = opener.read()
    imgurlPattern = re.compile(r'<img src=\"\.\./joyimages/(\d+\....)')
    if type(imgurlPattern.search(content)) == type(None):
        return 'none'
    else:
        matches = imgurlPattern.search(content).groups()
        return matches[0]

def LoadImageFilenames (imgFilenames):
    tmpHash = imgFilenames
    try:
        imgdb = open(IMGDB, 'r')
        for line in imgdb.readlines():
            url, fname = line.split(',')
            if url <> '':
                imgFilenames[url] = fname.rstrip('\r\n')
        imgdb.close()
    except IOError, ValueError:
        imgFilenames = tmpHash

def AppendImageFilename (url, fname):
    imgdb = open(IMGDB, 'a')
    imgdb.write('%s,%s\n' % (url, fname))
    imgdb.close()

def GetImageFilename (url, imgFilenames):
    if imgFilenames.has_key(url):
        return imgFilenames[url]
    else:
        fname = GetImageFilenameFromPage(url)
        AppendImageFilename(url, fname)
        imgFilenames[url] = fname
        return fname

def GetImageData ():
    fnameList = []
    pubdateList = []
    
    imgFilenames = {}
    LoadImageFilenames(imgFilenames)

    rssUrl = urllib.urlopen('http://feeds.feedburner.com/jotrepub')
    rss = minidom.parse(rssUrl)
    items = rss.getElementsByTagName('item')

    for item in items:
        permalinkUrl = item.getElementsByTagName('link')[0].childNodes[0].toxml()
        pubDate = item.getElementsByTagName('pubDate')[0].childNodes[0].toxml()

        # The images can be either gifs or jpegs, it's impossible
        # to tell without actually loading the page.
        fname = GetImageFilename(permalinkUrl, imgFilenames)
        if fname == 'none':
            pass # we couldn't find an image at this location
        else:
            fnameList.append(fname)
            pubdateList.append(pubDate)
    return fnameList, pubdateList

def RssHeader ():
    print """<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0">
    <channel>
    <title>The Joy of Tech</title>
    <link>http://www.geekculture.com/joyoftech/index.html</link>
    <description>The Joy of Tech Comic Strip</description>
    """

def RssBody (imageDataList):
    fnameList, pubdateList = imageDataList
    for imgdata in zip(fnameList, pubdateList):
        print """
            <item>
            <title>Issue %(issue)s</title>
            <description><![CDATA[ <img src="http://www.geekculture.com/joyoftech/joyimages/%(filename)s"
              alt="Joy of Tech Comic" /> ]]></description>
            <link>http://www.geekculture.com/joyoftech/joyarchives/%(issue)s.html</link>
            <pubDate>%(pubdate)s</pubDate>
            </item>""" % { 'issue': imgdata[0].split('.')[0], 'filename': imgdata[0], 'pubdate': imgdata[1] }

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

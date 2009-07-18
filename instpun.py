#!/usr/bin/python

# See LICENSE.txt in this source repository for terms of use.
# Synthesizes a full-text RSS feed for Instapundit.com

import os, sys, re, time
import codecs
import gzip, cStringIO
from BeautifulSoup import BeautifulSoup, NavigableString, Tag

VERSION = '0.8.0'
punct = ['.', ',', '!', ';', ':'] # global
curdate = '' # global


class FeedItem:
    """Represents a feed item."""
    
    def __init__ (self):
        self.posttitle = ''
        self.postcontent = ''
        self.postdate = ''
        self.postpermalink = ''
        self.postauthor = ''

    def __str__ (self):
        return u'Title: ' + self.posttitle + u'\n' \
               + u'Content: ' + self.postcontent + u'\n' \
               + u'Date: ' + self.postdate + u'\n' \
               + u'Link: ' + self.postpermalink + u'\n' \
               + u'Author: ' + self.postauthor + u'\n'
    
    
class WebDocConfig:
    Interval = 66 * 60 # 66 minutes
    Error = 1000
    Fresh = 1001
    Stale = 1002


def WebFetch (url, proxy=''):
    """Fetches a document from the web (with gzip encoding to save bandwidth).
    Returns the document as a string, or the empty string in case of error."""

    import urllib2
    try:
        if proxy != '':
            proxyHandler = urllib2.ProxyHandler({'http':proxy})
            opener = urllib2.build_opener(proxyHandler)
        else:
            opener = urllib2.build_opener()
        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        handle = opener.open(request)
        returnedData = handle.read()
        # print 'Fetched', len(returnedData), 'bytes.'
        # print 'Content Encoding:', handle.headers.get('Content-Encoding')
        encoding = handle.headers.get('Content-Encoding')
        if encoding != None and encoding.find('gzip') != -1:
            compressedStream = cStringIO.StringIO(returnedData)
            gzipper = gzip.GzipFile(fileobj=compressedStream)
            webdoc = gzipper.read()
        else:
            webdoc = returnedData
        return webdoc
    except: # BaseException, e:
        # print '* * * Exception:', e
        return ''


def GetFileAge (filename):
    """Returns the number of seconds since the file 'filename' was modified."""
    return time.time() - os.stat(filename)[8]


def RefreshWebDocCache (filename, url):
    """Checks that the cached on-disk 'filename' isn't stale.
    If it is, re-fetches from web."""
    ret = WebDocConfig.Error
    if (not(os.path.exists(filename)) or GetFileAge(filename) > WebDocConfig.Interval):
        webdoc = WebFetch(url)
        if webdoc != '':
            fh = open(filename, 'w')
            fh.write(webdoc)
            fh.close()
            ret = WebDocConfig.Fresh
    else:
        ret = WebDocConfig.Stale
    return ret


def CompressBuffer (buf):
    """Compresses a buffer using gzip, suitable for web delivery.
    Returns the compressed buffer."""
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', fileobj = zbuf, compresslevel = 9)
    zfile.write(buf)
    zfile.close()
    return zbuf.getvalue()


def AcceptsGzip ():
    """Checks if the HTTP client can accept gzip encoding. Suitable
    for CGI only, not mod_python. Returns 1 if gzip is supported."""
    ret = 0
    try:
        if string.find(os.environ["HTTP_ACCEPT_ENCODING"], "gzip") != -1:
            ret = 1
    except:
        pass
    return ret


def EmitRss (filename):
    """Reads RSS from 'filename' and outputs it. Tested with CGI only."""

    gzipOk = AcceptsGzip()
    # content expires in INTERVAL seconds
    exptime = time.strftime("%a, %d %b %Y %H:%M:%S UTC", \
                            time.gmtime(time.time() + WebDocConfig.Interval))
    fh = open(filename, 'rb')
    rss = fh.read()
    fh.close()

    sys.stdout.write("Content-Type: application/rss+xml\r\n")
    sys.stdout.write("Expires: %s\r\n" % exptime)
    if gzipOk:
        # gzip code from
        # http://www.xhaus.com/alan/python/httpcomp.html
        zbuf = CompressBuffer(rss)
        sys.stdout.write("Content-Encoding: gzip\r\n")
        sys.stdout.write("Content-Length: %d\r\n" % (len(zbuf)))
        sys.stdout.write("\r\n")
        sys.stdout.write(zbuf)
    else:
        sys.stdout.write("Content-Length: %d\r\n" % (len(rss)))
        sys.stdout.write("\r\n")
        sys.stdout.write(rss)


def PrintRssHeader (fh, feedpubdate):
    fh.write("""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:sy="http://purl.org/rss/1.0/modules/syndication/"
    xmlns:content="http://purl.org/rss/1.0/modules/content/">
    <channel>
    <title>Instapundit</title>
    <link>http://pajamasmedia.com/instapundit/</link>
    <description>Glenn Reynolds' blog offers opinions on current events, as well as humor and personal notes. (This is a synthesized feed.)</description>
    <dc:language>en-us</dc:language>
    <dc:creator>pundit@instapundit.com</dc:creator>
    <dc:rights>Copyright 2007-2009</dc:rights>
    <dc:date>%(feedpubdate)s</dc:date>
    <sy:updatePeriod>hourly</sy:updatePeriod>
    <sy:updateFrequency>1</sy:updateFrequency>
    <sy:updateBase>2000-01-01T12:00+00:00</sy:updateBase>

""" % { 'feedpubdate': feedpubdate })

# Instapundit doesn't do post titles so we make our own using a simple-minded algorithm:
# we look at the first 64 characters or so and try to find  sentence or any other appropriate fragment.
def MakeTitle (post):
    global punct
    postextract = post[0:256]
    lenextract = len(postextract) - 1
    txtrepr = ''
    st_suppress = False
    st_abracketstop = False
    for ix in range(0, 256):
        if ix > lenextract: break
        ch = postextract[ix]
        if ch == '<':
            st_suppress = True
            continue
        if st_suppress and ch == '>':
            st_suppress = False
            continue
        if ch == '\n' or ch == '\r' or ch == '\t': continue
        if not st_suppress: txtrepr += ch
    # print "*** Text extract: '%s'" % txtrepr

    txtrepr = txtrepr.strip()
    if txtrepr == '': 
        txtrepr = '(No Title)'
    if len(txtrepr) <= 64:
        return txtrepr
    postextract = txtrepr[0:64]
    spacefound = False
    ixSpace = 63
    ixPunct = -1
    
    for ix in range(62, -1, -1):
        ch = postextract[ix]
        if (not spacefound) and (ch == ' '):
            spacefound = True
            ixSpace = ix
        if ch in punct and postextract[ix+1] == ' ':
            ixPunct = ix
            break
    if ixPunct < 0: ixPunct = ixSpace
    return postextract[0:ixPunct+1] + " ..."
    
def PrintPost (fh, post):
    poststr = """
        <item>
            <title>%(posttitle)s</title>
            <guid>%(postlink)s</guid>
            <content:encoded><![CDATA[ %(postcontent)s
            ]]></content:encoded>
            <dc:date>%(postdatetime)s</dc:date>
            <dc:creator>%(postauthor)s</dc:creator>
        </item>
""".encode('utf-8')
    try:
        fh.write(poststr % { 'posttitle': post.posttitle, \
            'postlink': post.postpermalink, \
            'postcontent': post.postcontent, \
            'postdatetime': post.postdate, \
            'postauthor': post.postauthor })
    except UnicodeDecodeError:
        # print "***Error Printing:\n", repr(post.postcontent)
        errmsg = unicode('Unicode conversion error')
        fh.write(poststr % { 'posttitle': errmsg, \
            'postlink': errmsg, \
            'postcontent': errmsg, \
            'postdatetime': errmsg, \
            'postauthor': errmsg })



def ProcessTag (tag, feed):
    global curdate
    feedItem = FeedItem()
    t = tag
    if t != None:
        for c in t.findNext('div').contents:
            if isinstance(c, Tag):
                c2 = unicode(c)
                feedItem.postcontent += c2.encode('ascii', 'xmlcharrefreplace')
        feedItem.posttitle = MakeTitle(feedItem.postcontent)
    t = tag.findPrevious('div')
    if t != None and hasattr(t, 'class') and t['class'] == 'post-title':
        curdate = t.h2.string
    t = tag.findNext('p', 'post-meta')
    if t != None:
        s = t.contents[0].replace('Posted at ', '').replace(' by ', '')
        postdate = time.strptime(curdate + ' ' + s, "%B %d, %Y %I:%M %p")
        feedItem.postdate = time.strftime('%Y-%m-%dT%H:%M:00+00:00', postdate).encode('ascii', 'xmlcharrefreplace')
        feedItem.postpermalink = t.a['href'].encode('ascii', 'xmlcharrefreplace')
        feedItem.postauthor = t.strong.string.encode('ascii', 'xmlcharrefreplace')
    feed.append(feedItem)
   

def GetFeedItems (soup, feed):
    # look for the first post
    postelems = soup.findAll('div', 'post')
    if postelems != None:
        for post in postelems:
            ProcessTag(post, feed)

def ConvertToRss (sourceFile, rssFile):
    inf = codecs.open(sourceFile, 'r', 'utf-8')
    inhtml = inf.read()
    inf.close()
    soup = BeautifulSoup(inhtml)
    
    feed = []
    GetFeedItems(soup, feed)
    if len(feed) > 1:
        feedpubdate = feed[0].postdate
    else:
        feedpubdate = 'Unknown'
    outf = codecs.open(rssFile, 'w', 'utf-8')
    PrintRssHeader(outf, feedpubdate)
    for item in feed:
        PrintPost(outf, item)
    outf.write("</channel></rss>\r\n")
    outf.close()


def MakeRss (sourceFilename, rssFilename):
    """Re-creates the 'rssFilename' on disk if 'sourceFilename' is out of date."""

    ret = RefreshWebDocCache(sourceFilename, 'http://pajamasmedia.com/instapundit/')
    if not(os.path.exists(rssFilename)) or ret == WebDocConfig.Fresh:
        ConvertToRss(sourceFilename, rssFilename)


def Main ():
    MakeRss('tmp-instpun-in.html', 'tmp-instpun-out-rss.xml')
    EmitRss('tmp-instpun-out-rss.xml')

if __name__ == '__main__':
    Main()

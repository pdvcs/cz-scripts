#!/usr/bin/python

# See LICENSE.txt in this source repository for terms of use.
# Synthesizes full RSS feeds, with permalinks, for http://technews.acm.org

# UPDATE - technews.acm.org has changed their presentation logic and now
# generates full RSS feeds, so this code no longer works and is no longer
# necessary.

import os
from time import strftime, strptime
import WebFetch
from BeautifulSoup import BeautifulSoup, NavigableString, Tag

PDX_ACMTECH_VERSION = '0.1.0'

# === HTML Scraping =============================

class FeedItemPart:
    Head = 1
    Body = 2
    
class FeedItemListMaker:
    """Represents a list of feed items."""
    
    def __init__ (self):
        self.items = []
        self.itempair = [None, None]
        
    def add (self, item, type):
        if type == FeedItemPart.Head:
            self.itempair[0] = item
        elif type == FeedItemPart.Body:
            self.itempair[1] = item
        else:
            print "Unknown type passed!"
        if self.itempair[0] != None and self.itempair[1] != None:
            self.items.append( (self.itempair[0], self.itempair[1]) )
            self.itempair[0] = None
            self.itempair[1] = None

            
def ParseHeadline (tag):
    title = ''
    id = ''
    byline = ''
    node = tag.find('a')
    if node != None:
        title = node.contents[0].strip()
        title = title.replace("\n", "")
        id = node['name']
    node = tag.find('br')
    if node != None:
        node = node.nextSibling
        byline = str(node).strip().replace("\n", "")
    # print "*** title:", title, "\n*** byline:", byline, "\n*** id:", id
    return (title, byline, id)

def ParseContentItem (tag):
    link = ''
    item = tag.contents[0].strip()
    node = tag.find('a')
    if node != None:
        link = node['href']
        link = link.replace("\n", "")
    # print "*** item:", item, "\n*** link:", link
    return (item, link)

def ProcessTag (tag, feed):
    ret = tag
    if isinstance(tag.contents[1], Tag) and tag.contents[1].name == "b":
        # a headline
        feedElement = ParseHeadline(tag)
        feed.add(feedElement, FeedItemPart.Head)
    elif isinstance(tag.contents[0], NavigableString) and len(tag.contents[0]) > 3:
        # content item
        feedElement = ParseContentItem(tag)
        feed.add(feedElement, FeedItemPart.Body)
    else:
        # we've reached the end of useful information on the page,
        # break out of the loop
        ret = None
    return ret

def GetFeedItems (soup, feed):
    # look for the first headline
    tag = soup.find('span', { "class" : "bodytext" })
    if tag != None:
        ProcessTag(tag, feed)

    while tag != None:
        # go to the next tag
        tag = tag.nextSibling
        if tag != None:
            if hasattr(tag, 'name') and tag.name == 'p':
                if isinstance(tag.contents[0], Tag) \
                    and tag.contents[0].name == "hr":
                    # ignore tags with just an <hr> in them
                    pass
                else:
                    tag = ProcessTag(tag, feed)

def GetFeedIssueDate (soup):
    ret = None
    # look for the current issue date
    tag = soup.find('div', { "class" : "regtextTitle" })
    if tag != None:
        node = tag.find(text="Current Issue:")
        node = node.next
        issuedatestr = node.strip().split("&nbsp;")[0]
        try:
            ret = strptime(issuedatestr, "%b. %d, %Y")
        except:
            pass
    return ret  

# === RSS Output =============================

def PrintRssHeader (fh, feedpubdate):
    fh.write("""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:sy="http://purl.org/rss/1.0/modules/syndication/"
    xmlns:content="http://purl.org/rss/1.0/modules/content/">
    <channel>
    <title>ACM TechNews</title>
    <link>http://technews.acm.org/</link>
    <description>Timely Topics for IT Professionals from the ACM (This is a synthesized feed.)</description>
    <dc:language>en-us</dc:language>
    <dc:creator>technews@hq.acm.org</dc:creator>
    <dc:date>%(feedpubdate)s</dc:date>
    <sy:updatePeriod>daily</sy:updatePeriod>
    <sy:updateFrequency>2</sy:updateFrequency>
    <sy:updateBase>2008-09-01T00:00+00:00</sy:updateBase>

""" % { 'feedpubdate': feedpubdate })


def PrintPost (fh, posttitle, postlink, postcontent, postdatetime, postauthor):
    fh.write("""
        <item>
            <title>%(posttitle)s</title>
            <guid>%(postlink)s</guid>
            <content:encoded><![CDATA[ %(postcontent)s
            ]]></content:encoded>
            <dc:date>%(postdatetime)s</dc:date>
            <dc:creator>%(postauthor)s</dc:creator>
        </item>
""" % { 'posttitle':posttitle, 'postlink':postlink, \
        'postcontent':postcontent, 'postdatetime':postdatetime, \
        'postauthor':postauthor })

def MakePermalink (issuedate, postAnchorId):
    # if the issue date is Aug 27 2008 and the anchor id is 376665,
    # then the permalink is
    # http://technews.acm.org/archives.cfm?fo=2008-08-Aug/Aug-27-2008.html#376665
    return strftime('http://technews.acm.org/archives.cfm?fo=%Y-%m-%b/%b-%d-%Y.html#', issuedate) + postAnchorId

# === RSS Conversion =============================
    
def ConvertToRss (sourceFile, rssFile):
    input = open(sourceFile, 'r')
    acmhtml = input.read()
    input.close()
    soup = BeautifulSoup(acmhtml)

    feed = FeedItemListMaker()
    GetFeedItems(soup, feed)
    issuedate = GetFeedIssueDate(soup)
    issuedatestr = strftime('%Y-%m-%dT%H:%M:00+00:00', issuedate)
    
    outf = open(rssFile, 'w')
    PrintRssHeader(outf, issuedatestr)
    for item in feed.items:
        (head, body) = item
        permalink = MakePermalink(issuedate, head[2])
        content = body[0] + '<br><a href="' + body[1] + '">Read more...</a>'
        PrintPost(outf, posttitle=head[0], postlink=permalink, postcontent=content, postdatetime=issuedatestr, postauthor=head[1])
        # print "*** title:", head[0], "\n*** byline:", head[1], "\n*** id:", head[2]
        # print "*** item:", body[0], "\n*** link:", body[1], "\n----"

    outf.write("</channel></rss>\r\n")
    outf.close()


def MakeRss (sourceFilename, rssFilename, cache):
    """Re-creates the 'rssFilename' on disk if 'sourceFilename' is out of date."""

    ret = WebFetch.RefreshWebDocCache( \
        sourceFilename, 'http://technews.acm.org/', cache) 
    if not(os.path.exists(rssFilename)) or ret == WebFetch.CacheConfig.Fresh:
        ConvertToRss(sourceFilename, rssFilename)


def Main ():
    feedcache = WebFetch.CacheConfig(24 * 60 * 60)
    MakeRss('tmp-acmtech-in.html', 'tmp-acmtech-out-rss.xml', feedcache)
    WebFetch.EmitRss('tmp-acmtech-out-rss.xml', feedcache)

if __name__ == '__main__':
    Main()

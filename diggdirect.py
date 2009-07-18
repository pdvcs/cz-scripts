#!/usr/bin/python

# See LICENSE.txt in this source repository for terms of use.
# Synthesizes a 'better' RSS feed for Digg, with direct links to
# linked stories and a separate link to comments.

import os, sys, time, string
import gzip, cStringIO

# ---------------------------------------------------------------------

DIGGURL = 'http://services.digg.com/stories/popular?appkey=http%3A%2F%2Fwww.chaoszone.org%2Fcode%2Fdigg%2F&type=xml&count=50'
INTERVAL = 33 * 60 # 33 minutes
VERSION = '1.0.5'

# ---------------------------------------------------------------------

def WebFetch ():
    """Fetches a document from the web (with gzip encoding to save bandwidth).
    Returns the document as a string, or the empty string in case of error."""

    import urllib2

    try:    
        request = urllib2.Request(DIGGURL)
        request.add_header('Accept-encoding', 'gzip')
        opener = urllib2.build_opener()
        handle = opener.open(request)
        compressedData = handle.read()
        # print 'Fetched', len(compressedData), 'bytes.'
        compressedStream = cStringIO.StringIO(compressedData)
        gzipper = gzip.GzipFile(fileobj=compressedStream)
        xml = gzipper.read()
        return xml
    except:
        return ''

# ---------------------------------------------------------------------

def GetFileAge (filename):
    """Returns the number of seconds since the file 'filename' was modified."""
    return time.time() - os.stat(filename)[8]

def GetXml (filename):
    ret = 0
    if (not(os.path.exists(filename)) or GetFileAge(filename) > INTERVAL):
        xml = WebFetch()
        if xml <> '':
            fh = open(filename, 'w')
            fh.write(xml)
            fh.close()
            ret = 1
    else:
        ret = 2
    return ret

# ---------------------------------------------------------------------

def GetDiggStoryItems (xmlfile):
    """# Parses Digg's /stories/popular XML and returns a hashtable containing
    (title, link, description, etc) for all stories, and the xml publish time
    as a string."""

    from xml.dom import minidom

    storyList = []
    xmltree = minidom.parse(xmlfile)
    items = xmltree.getElementsByTagName('story')
    for item in items:
        title = item.getElementsByTagName('title')[0].childNodes[0].nodeValue
        link = item.getAttribute('link')
        guid = item.getAttribute('href')
        diggcount = item.getAttribute('diggs')
        commentcount = item.getAttribute('comments')
        pubDate = time.strftime("%a, %d %b %Y %H:%M:%S +0000", \
                    (time.gmtime(int(item.getAttribute('promote_date')))))
        container = item.getElementsByTagName('container')[0].getAttribute('name')
        topic = item.getElementsByTagName('topic')[0].getAttribute('name')
        submitter = item.getElementsByTagName('user')[0].getAttribute('name')
        description = item.getElementsByTagName('description')[0].childNodes[0].nodeValue
        storyList.append({'title':title, 'link':link, 'guid':guid, \
          'diggcount':diggcount, 'commentcount':commentcount, \
          'pubDate':pubDate, 'container':container, 'submitter':submitter, \
          'topic':topic, 'description':description })

    feedpubDate = time.strftime("%a, %d %b %Y %H:%M:%S +0000", (time.gmtime(int(
        xmltree.getElementsByTagName('stories')[0].getAttribute('timestamp') ))))
    return storyList, feedpubDate

# ---------------------------------------------------------------------

def AddToItem (dom, parent, element_title, text, asCdata=0, attribs={}):
    """Adds a child text (or optionally CDATA) node to a parent (usually <item>)
    element. Optionally also adds attributes."""

    parent.appendChild(dom.createTextNode('\n'))
    elem = dom.createElement(element_title)
    if asCdata:
        elem.appendChild(dom.createCDATASection(text))
    else:
        elem.appendChild(dom.createTextNode(text))
    if len(attribs) > 0:
        for key in attribs.keys():
            elem.setAttribute(key, attribs[key])
    parent.appendChild(elem)

# ---------------------------------------------------------------------

def MakePostContent (href, diggcount, commentcount, container, topic, desc):
    """Uses the given parameters to create formatted text suitable for
    insertion into a post's <content:encoded> element. Returns the formatted
    text as a unicode string."""

    data = u"""<p>%(desc)s</p>
<p><small>
    <a href="%(href)s">%(comments)s comments</a>,
    %(diggs)s diggs.
    Category: %(container)s/%(topic)s.
</small></p>
""" % \
    { 'desc':desc, 'href':href, 'comments':commentcount, \
      'diggs':diggcount, 'container':container, 'topic':topic }
    
    return data

# ---------------------------------------------------------------------

def ConvertToRss (xmlfile, rssfile):
    """Converts Digg's /stories/popular XML from 'xmlfile' to RSS2
    and writes 'rssfile' to disk."""

    from xml.dom import minidom

    storyList, feedpubDate = GetDiggStoryItems(xmlfile)
    rssStub = u"""\
<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
    xmlns:slash="http://purl.org/rss/1.0/modules/slash/"
    xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
    <title>Digg Direct</title>
    <link>http://digg.com</link>
    <description>A synthesized feed with direct links to popular digg stories. Created using Digg's Services API.</description>
    <ttl>33</ttl>
    <pubDate>%(pubdate)s</pubDate>
    <generator>diggdirect.py v%(version)s</generator>
    <language>en</language>
</channel>
</rss>""" % { 'pubdate':feedpubDate, 'version':VERSION }
    rsstree = minidom.parseString(rssStub.encode('utf-8'))
    channel = rsstree.getElementsByTagName('channel')[0]
    for story in storyList:
        itemElem = rsstree.createElement('item')
        AddToItem(rsstree, itemElem, 'title', story['title'])
        AddToItem(rsstree, itemElem, 'link', story['link'])
        AddToItem(rsstree, itemElem, 'guid', story['guid'], attribs={'isPermaLink':'false'})
        AddToItem(rsstree, itemElem, 'pubDate', story['pubDate'])
        AddToItem(rsstree, itemElem, 'comments', story['guid'])
        AddToItem(rsstree, itemElem, 'dc:creator', story['submitter'])
        AddToItem(rsstree, itemElem, 'category', story['container'], asCdata=1)
        AddToItem(rsstree, itemElem, 'slash:comments', story['commentcount'])
        AddToItem(rsstree, itemElem, 'description', story['description'])
        AddToItem(rsstree, itemElem, 'content:encoded', \
            MakePostContent(
                story['guid'], story['diggcount'], story['commentcount'], \
                story['container'], story['topic'], story['description'] \
            ), \
            asCdata=1)
        channel.appendChild(itemElem)

    try:
        rssfh = open(rssfile, 'wb')
        rssfh.write(rsstree.toxml(encoding='utf-8'))
        rssfh.close()
    except IOError, e:
        # print 'IO Error:', e
        rssfh.close()
    except UnicodeDecodeError, e:
        # print 'Unicode Error:', e
        rssfh.close()
    except:
        # print 'Unexpected error!'
        # no "finally" until Python 2.5, which Dreamhost doesn't yet have... :-(
        rssfh.close()

# ---------------------------------------------------------------------

def MakeRss (xmlFilename, rssFilename):
    """Re-creates the 'rssFilename' on disk if 'xmlFilename' is out of date."""

    ret = GetXml(xmlFilename)
    if not(os.path.exists(rssFilename)) or ret == 1:
        ConvertToRss(xmlFilename, rssFilename)

# ---------------------------------------------------------------------

def CompressBuffer (buf):
    """Compresses a buffer using gzip, suitable for web delivery.
    Returns the compressed buffer."""
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', fileobj = zbuf, compresslevel = 9)
    zfile.write(buf)
    zfile.close()
    return zbuf.getvalue()

# ---------------------------------------------------------------------

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

# ---------------------------------------------------------------------

def EmitRss (filename):
    """Reads RSS from 'filename' and outputs it. Tested with CGI only."""

    gzipOk = AcceptsGzip()
    # content expires in INTERVAL seconds
    exptime = time.strftime("%a, %d %b %Y %H:%M:%S UTC", \
                            time.gmtime(time.time() + INTERVAL))
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

# ---------------------------------------------------------------------

def Main ():
    """The main entry-point into the program."""
    MakeRss('tmp-diggpop.xml', 'tmp-diggpop-rss.xml')
    EmitRss('tmp-diggpop-rss.xml')

# ---------------------------------------------------------------------

if __name__ == '__main__':
    Main()


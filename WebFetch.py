#!/usr/bin/python

# See LICENSE.txt in this source repository for terms of use.
# Module to handle fetching web pages and maintaining a simple cache

import os, sys, time
import gzip

PDX_WEBFETCH_VERSION = '0.2.0'

class CacheConfig:
    """Class that defines caching parameters."""
    
    def __init__ (self, retentionTime):
        """How long to retain cached data, in seconds."""
        self.RetentionPeriod = retentionTime
        
    Error = 1000
    Fresh = 1001
    Stale = 1002


def WebFetch (url, proxy=''):
    """Fetches a document from the web (with gzip encoding to save bandwidth).
    Returns the document as a string, or the empty string in case of error."""

    import urllib2, cStringIO
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


def RefreshWebDocCache (filename, url, cache, proxy=''):
    """Checks that the cached on-disk 'filename' isn't stale.
    If it is, re-fetches from web."""
    ret = CacheConfig.Error
    if (not(os.path.exists(filename)) or GetFileAge(filename) > cache.RetentionPeriod):
        webdoc = WebFetch(url, proxy)
        if webdoc != '':
            fh = open(filename, 'w')
            fh.write(webdoc)
            fh.close()
            ret = CacheConfig.Fresh
    else:
        ret = CacheConfig.Stale
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

def EmitRss (filename, cache):
    """Reads RSS from 'filename' and outputs it. Tested with CGI only."""

    gzipOk = AcceptsGzip()
    # content expires in cache.RetentionPeriod seconds
    exptime = time.strftime("%a, %d %b %Y %H:%M:%S UTC", \
        time.gmtime(time.time() + cache.RetentionPeriod))
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


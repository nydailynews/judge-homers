#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Return recent items from a json feed. Recent means "In the last X days."
import os
import doctest
import json
import urllib2
import argparse
import types
import gzip
from datetime import datetime, timedelta
from time import mktime

class RecentJson:
    """ Methods for ingesting and publishing JSON feeds.
        >>> rj = RecentJson()
        >>> rj.get('')
        True
        >>> rj.parse()
        """

    def __init__(self, args={}):
        self.args = args
        if not hasattr(self.args, 'days'):
            self.args.days = 0
        self.days = self.args.days

    def get(self, url):
        """ Wrapper for API requests. Take a URL, return a json array.
            >>> url = 'http://www.nydailynews.com/json/cmlink/aaron-judge-1.3306628'
            >>> parser = build_parser()
            >>> args = parser.parse_args([url])
            >>> rj = RecentJson(args)
            >>> rj.get(url)
            True
            >>> rj.parse()
            #>>> articles = rj.recently()
            """
        response = urllib2.urlopen(url)
        if int(response.code) >= 400:
            if 'verbose' in self.args and self.args.verbose:
                print "URL: %s" % url
            raise ValueError("URL %s response: %s" % (url, response['status']))
        self.xml = response.read()
        return True

    def parse(self):
        """ Turn the xml into an object.
            """
        try:
            p = json.loads(self.xml)
        except:
            fh = open('json.gz', 'wb')
            fh.write(self.xml)
            fh.close()
            p = json.loads(gzip.GzipFile('json.gz', 'r').read())
        self.p = p
        return p

    def recently(self):
        """ Return a feedparser entry object for the last X days of feed entries.
            """
        items = []
        for item in self.p:
            items.append(item)

        return items
        for item in self.p:
            # print item.keys()
            # [u'body', u'tags', u'url', u'contentId', u'abstract', u'author', u'lastUpdated', u'mobileTitle', u'mobileUrl', u'publish_date', u'images', u'title', u'type', u'categories']
            print item['publish_date']
            # Fri, 7 Jul 2017 15:16:38 -0400
            dt = datetime.strptime(item['publish_date'], '%a, %d %b %Y %X %z')
            delta = datetime.today() - dt

            if delta.days > int(self.days):
                continue
            items.append(item)
            if 'verbose' in self.args and self.args.verbose:
                print delta.days, dt
        self.items = items
        return items

def main(args):
    """ For command-line use.
        """
    rj = RecentJson(args)
    if args:
        articles = []
        for arg in args.urls[0]:
            if args.verbose:
                print arg
            rj.get(arg)
            rj.parse()
            articles.append(rj.recently())


        for i, article in enumerate(articles[0]):
            if i > args.limit and args.limit > 0:
                break 

            if args.output == 'html':
                if type(article['title']) is types.UnicodeType:
                    article['title'] = article['title'].encode('utf-8', 'replace')
                print '<li><a href="{0}">{1}</a></li>'.format(article['url'], article['title'])
            elif args.output == 'json':
                print json.dumps({'title': article['title'],
                    'id': article['id'],
                    'description': article['description']})
            elif args.output == 'csv':
                dt = datetime.fromtimestamp(mktime(article.published_parsed))
                article['datetime'] = '%s-%s-%s' % (dt.year, dt.month, dt.day)
                if dt.month < 10:
                    article['datetime'] = '%d-0%d-%d' % (dt.year, dt.month, dt.day)
                    if dt.day < 10:
                        article['datetime'] = '%d-0%d-0%d' % (dt.year, dt.month, dt.day)
                article['slug'] = article['title'].lower().replace(' ', '-').replace('--', '-').replace(':', '')
                article['iframe_url'] = article['media_player']['url']
                article['image_url'] = article['media_thumbnail'][0]['url']
                article['image_large_url'] = article['media_thumbnail'][1]['url']
                article['description'] = article['description'].replace('"', "'")
                # date,title,id,slug,player_url,image_url,image_large_url,keywords,description
                print '%(datetime)s,"%(title)s",%(id)s,%(slug)s,%(iframe_url)s,%(image_url)s,%(image_large_url)s,"%(media_keywords)s","%(description)s"' % article


def build_parser():
    """ We put the argparse in a method so we can test it
        outside of the command-line.
        """
    parser = argparse.ArgumentParser(usage='$ python recentfeed.py http://domain.com/rss/',
                                     description='''Takes a list of URLs passed as args.
                                                  Returns the items published today unless otherwise specified.''',
                                     epilog='')
    parser.add_argument("-v", "--verbose", dest="verbose", default=False, action="store_true")
    parser.add_argument("-d", "--days", dest="days", default=0)
    parser.add_argument("-l", "--limit", dest="limit", default=0, type=int)
    parser.add_argument("-o", "--output", dest="output", default="html", type=str)
    parser.add_argument("urls", action="append", nargs="*")
    return parser

if __name__ == '__main__':
    """ 
        """
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        doctest.testmod(verbose=args.verbose)

    main(args)

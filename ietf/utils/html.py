# Copyright The IETF Trust 2010-2020, All Rights Reserved
# -*- coding: utf-8 -*-
# Taken from http://code.google.com/p/soclone/source/browse/trunk/soclone/utils/html.py
"""Utilities for working with HTML."""


import bleach
import copy
import html2text
import lxml.etree
import lxml.html
import lxml.html.clean

import debug                            # pyflakes:ignore

from django import forms
from django.utils.functional import keep_lazy

from ietf.utils.mime import get_mime_type


# Allow the protocols/tags/attributes we specifically want, plus anything that bleach declares
# to be safe. As of 2025-01-27, the explicit lists for protocols and tags are a strict superset
# of bleach's defaults.
acceptable_protocols = bleach.sanitizer.ALLOWED_PROTOCOLS.union(
    {"http", "https", "mailto", "ftp", "xmpp"}
)
acceptable_tags = bleach.sanitizer.ALLOWED_TAGS.union(
    {
        # fmt: off
        "a", "abbr", "acronym", "address", "b", "big",
        "blockquote", "body", "br", "caption", "center", "cite", "code", "col",
        "colgroup", "dd", "del", "dfn", "dir", "div", "dl", "dt", "em", "font",
        "h1", "h2", "h3", "h4", "h5", "h6", "head", "hr", "html", "i", "ins", "kbd",
        "li", "ol", "p", "pre", "q", "s", "samp", "small", "span", "strike", "style",
        "strong", "sub", "sup", "table", "title", "tbody", "td", "tfoot", "th", "thead",
        "tr", "tt", "u", "ul", "var"
        # fmt: on
    }
)
acceptable_attributes = bleach.sanitizer.ALLOWED_ATTRIBUTES | {
    "*": ["id"],
    "ol": ["start"],
}


# Instantiate sanitizer classes
_bleach_cleaner = bleach.sanitizer.Cleaner(
    tags=acceptable_tags,
    attributes=acceptable_attributes,
    protocols=acceptable_protocols,
    strip=True,
)


_liberal_bleach_cleaner = bleach.sanitizer.Cleaner(
    tags=acceptable_tags.union({"img", "figure", "figcaption"}),
    attributes=acceptable_attributes | {"img": ["src", "alt"]},
    protocols=acceptable_protocols,
    strip=True,
)


def clean_html(text):
    return _bleach_cleaner.clean(text)


def liberal_clean_html(text):
    return _liberal_bleach_cleaner.clean(text)


@keep_lazy(str)
def remove_tags(html, tags):
    """Returns the given HTML sanitized, and with the given tags removed."""
    allowed = acceptable_tags - set(t.lower() for t in tags)
    return bleach.clean(html, tags=allowed, strip=True)

# ----------------------------------------------------------------------
# Html fragment cleaning

def sanitize_fragment(html):
    return _bleach_cleaner.clean(html)

# ----------------------------------------------------------------------
# Page cleaning


class Cleaner(lxml.html.clean.Cleaner):
    charset = 'utf-8'
    def __init__(self, charset='utf-8', **kw):
        self.charset = charset
        super(Cleaner, self).__init__(**kw)
        
    # Copied from lxml 4.2.0 and modified to insert charset meta:
    def clean_html(self, html):
        result_type = type(html)
        if isinstance(html, (str, bytes)):
            doc = lxml.html.fromstring(html)
        else:
            doc = copy.deepcopy(html)
        self(doc)
        head = doc.find('head')
        if head != None:
            meta = lxml.etree.Element('meta', charset=self.charset)
            meta.tail = '\n'
            head.insert(0, meta)
        return lxml.html._transform_result(result_type, doc)

# We will be saving as utf-8 later, so set that in the meta tag.
lxml_cleaner = Cleaner(allow_tags=acceptable_tags, remove_unknown_tags=None, style=False, page_structure=False, charset='utf-8')

def sanitize_document(html):
    return lxml_cleaner.clean_html(html)


# ----------------------------------------------------------------------
# Text field cleaning

def clean_text_field(text):
    mime_type, encoding = get_mime_type(text.encode('utf8'))
    if   mime_type == 'text/html': #  or re.search(r'<\w+>', text):
        text = html2text.html2text(text)
    elif mime_type in ['text/plain', 'application/x-empty', ]:
        pass
    else:
        raise forms.ValidationError("Unexpected text field mime type: %s" % mime_type)
    return text
    

def unescape(text):
    """
    Returns the given text with ampersands, quotes and angle brackets decoded
    for use in URLs.

    This function undoes what django.utils.html.escape() does
    """
    return text.replace('&amp;', '&').replace('&#39;', "'").replace('&quot;', '"').replace('&gt;', '>').replace('&lt;', '<' )



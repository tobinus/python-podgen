# -*- coding: utf-8 -*-
"""
    podgen.transcript
    ~~~~~~~~~~~~~~~

    This module contains Transcript, which represents an episode transcript.

    :copyright: 2021, Slim Beji <mslimbeji@gmail.com>
    :license: FreeBSD and LGPL, see license.* for more details.
"""
# Support for Python 2.7
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *
from future.moves.urllib.parse import urlparse

import sys
import warnings

import pycountry
import validators

from podgen.warnings import NotSupportedByItunesWarning


class Transcript(object):
    """Immutable class representing an Episode transcript.

    By using this class, you can be sure that the transcript object is formatted correctly.

    See https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md#transcript
    for an overview of the transcript tag

    Example::

        >>> from podgen import Transcript
        >>> t = Transcript("https://examples.com/transcript_sample.txt", "text/html", language="es", is_caption=False)
        >>> t.url
        https://examples.com/transcript_sample.txt
        >>> t.type
        text/html
        >>> t.language
        es
        >>> t.is_caption
        False
        >>>
        >>> t = Transcript("https://examples.com/transcript_sample_2.txt", "text/txt")
        >>> t.url
        https://examples.com/transcript_sample_2.txt
        >>> t.type
        text/txt
    """

    _accepted_types = [
        "text/plain", "text/html", "text/vtt", "text/srt",
        "application/srt", "application/json"
    ]

    def __init__(self, url, type_, language=None, is_caption=False):
        """Create new Transcript object. See the class description of
        :class:´~podgen.transcript.Transcript`.

        :param url: Url of the transcript (Must be a valid url).
        :type url: str
        :param type: Mime type of the transcript file.
        :type type: str
        :param language: (Optional) Language of the transcript.
        :type language: str or None
        :param is_caption: (Optional) Set to True if the linked
        file is considered to be a closed captions file
        :type is_caption: bool
        """

        self._url = None
        self._type = None
        self._language = None
        self._is_caption = None

        self.url = url
        self.type = type_
        self.language = language
        self.is_caption = is_caption

    @property
    def url(self):
        """The URL at which this transcript is publicly accessible.

        Only absolute URLs are allowed, so make sure it starts with http:// or
        https://. The server should support HEAD-requests and byte-range
        requests.

        Ensure you quote parts of the URL that are not supposed to carry any
        special meaning to the browser, typically the name of your file.
        Common offenders include the slash character when not used to separate
        folders, the hash mark (#) and the question mark (?). Use
        :func:`urllib.parse.quote` in Python3 and :func:`urllib.quote` in
        Python2.

        :type: :obj:`str`
        """
        return self._url

    @url.setter
    def url(self, url):
        if not url:
            raise ValueError("url cannot be empty or None")

        if validators.url(url) is not True:
            raise ValueError("Not a valid url: %s" % url)

        parsed_url = urlparse(url)
        if parsed_url.scheme not in ("http", "https"):
            warnings.warn("URL scheme %s is not supported by iTunes. Make sure "
                          "you use absolute URLs and HTTP or HTTPS."
                          % parsed_url.scheme, NotSupportedByItunesWarning,
                          stacklevel=2)
        self._url = url

    @property
    def type(self):
        """The Mime type of the linked file (~.Transcript.url).
        https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md#transcript

        :type: :obj:`str`
        """
        return self._type

    @type.setter
    def type(self, type_):
        if not type_:
            raise ValueError("Transcript type cannot be empty or None")

        type_ = type_.lower()
        if type_ not in self._accepted_types:
            raise ValueError(
                "Transcript type must be one of %r, received %r instead"
                % (self._accepted_types, type_)
            )

        self._type = type_

    @property
    def language(self):
        """The language of the linked transcript.
        https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md#transcript

        :type: :obj:`str` or `None`
        """
        return self._language

    @language.setter
    def language(self, language):
        # pycountry does not work in python 2 anymore
        version = sys.version_info[0]
        if language and version !=2:
            language_country = language.split("-")
            language = language_country[0]
            if len(language_country) > 1:
                country = language_country[1]
            else:
                country = None

            try:
                language = pycountry.languages.lookup(language).alpha_2
            except:
                raise ValueError("Language code %r is unknown" % language)

            if country:
                try:
                    country = pycountry.countries.lookup(country).alpha_2
                    self._language = language + "-" + country
                except:
                    raise ValueError("Country code %r is unknown" % country)
            else:
                self._language = language

        else:
            if language:
                # python2 case
                self._language = language
            else:
                self._language = None

    @property
    def is_caption(self):
        """If set to True, the linked file is considered to be a closed captions file,
        regardless of what the mime type is. In that scenario, time codes are assumed
        to be present in the file in some capacity
        https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md#transcript

        :type: :obj:`bool`
        """
        return self._is_caption

    @is_caption.setter
    def is_caption(self, is_caption):
        if not isinstance(is_caption, bool):
            raise ValueError(
                "is_caption must be a boolean. Received object of type %r instead"
                % type(is_caption)
            )
        self._is_caption = is_caption

    def __repr__(self):
        return 'Transcript(url=%s, type=%s, language=%s, is_caption=%s)' % \
               (self.url, self.type, self.language, self.is_caption)

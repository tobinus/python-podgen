# -*- coding: utf-8 -*-
"""
    podgen.tests.test_person
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Test the Transcript class, which represents an episode transcript.

    :copyright: 2021, Slim Beji <mslimbeji@gmail.com>
    :license: FreeBSD and LGPL, see license.* for more details.
"""
# Support for Python 2.7
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *

import sys
import unittest
import warnings
from podgen import Transcript, NotSupportedByItunesWarning

class TestTranscript(unittest.TestCase):
    def setUp(self):
        self.url = "https://examples.com/transcript_sample.txt"
        self.type = "text/html"
        self.language_code = "es-US"
        self.is_caption = True
        self.version = sys.version_info[0]

    def _transcript(self):
        return Transcript(
            self.url,
            self.type,
            language_code=self.language_code,
            is_caption=self.is_caption
        )

    def test_OnlyUrlAndType(self):
        t = Transcript(self.url, self.type)
        assert t.url == self.url
        assert t.type == self.type
        assert t.language_code is None
        assert t.is_caption is False

    def test_isCaption(self):
        t = Transcript(self.url, self.type, is_caption=True)
        assert t.url == self.url
        assert t.type == self.type
        assert t.language_code is None
        assert t.is_caption is True

    def test_languageCode(self):
        t = Transcript(self.url, self.type, language_code=self.language_code)
        assert t.url == self.url
        assert t.type == self.type
        assert t.language_code == self.language_code
        assert t.is_caption is False

    def test_languageAndIsCaption(self):
        t = Transcript(
            self.url,
            self.type,
            is_caption=self.is_caption,
            language_code=self.language_code
        )
        assert t.url == self.url
        assert t.type == self.type
        assert t.language_code == self.language_code
        assert t.is_caption == self.is_caption

    def test_settingUrl(self):
        other_url = "https://examples.com/transcript_sample_2.txt"
        t = self._transcript()
        t.url = other_url
        assert t.url == other_url
        assert t.type == self.type
        assert t.language_code == self.language_code
        assert t.is_caption == self.is_caption

    def test_settingType(self):
        other_type = "application/json"
        t = self._transcript()
        t.type = other_type
        assert t.url == self.url
        assert t.type == other_type
        assert t.language_code == self.language_code
        assert t.is_caption == self.is_caption

    def test_settingLanguageCode(self):
        other_language = "fr-CA"
        t = self._transcript()
        t.language_code = other_language
        assert t.url == self.url
        assert t.type == self.type
        assert t.language_code == other_language
        assert t.is_caption == self.is_caption

        t.language_code = None
        assert t.url == self.url
        assert t.type == self.type
        assert t.language_code == None
        assert t.is_caption == self.is_caption

    def test_languageCaseInsensitive(self):
        if self.version == 2:
            assert True
        else:
            t = self._transcript()
            t.language_code = "fR-cA"
            assert t.language_code == "fr-CA"

    def test_settingIsCaption(self):
        other_caption_option = False
        t = self._transcript()
        t.is_caption = other_caption_option
        assert t.url == self.url
        assert t.type == self.type
        assert t.language_code == self.language_code
        assert t.is_caption == other_caption_option

        old_caption_option = t.is_caption
        t.is_caption = not old_caption_option
        assert t.url == self.url
        assert t.type == self.type
        assert t.language_code == self.language_code
        assert t.is_caption != old_caption_option

    def test_missingUrl(self):
        self.assertRaises(ValueError, Transcript, None, self.type)

    def test_warningMissingHttp(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            missing_http = "ftp://examples.com/transcript_sample_2.txt"
            t = self._transcript()
            t.url = missing_http
            assert len(w)==1
            assert issubclass(w[-1].category, NotSupportedByItunesWarning)


    def test_wrongUrl(self):
        self.assertRaises(ValueError, Transcript, "Not an actual url", self.type)

    def test_missingType(self):
        self.assertRaises(ValueError, Transcript, self.url, None)

    def test_wrongType(self):
        self.assertRaises(ValueError, Transcript, self.url, "Wrong type")

    def test_wrongLanguage(self):
        if self.version == 2:
            assert True
        else:
            self.assertRaises(ValueError, Transcript, self.url, self.type, "aaa")
            self.assertRaises(ValueError, Transcript, self.url, self.type, "en-aaa")

    def test_wronCaptionOption(self):
        self.assertRaises(ValueError, Transcript, self.url, self.type, is_caption="Not a boolean")

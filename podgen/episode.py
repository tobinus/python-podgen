# -*- coding: utf-8 -*-
"""
    podgen.episode
    ~~~~~~~~~~~~~~

    :copyright: 2013, Lars Kiesow <lkiesow@uos.de> and 2016, Thorben Dahl
        <thorben@sjostrom.no>

    :license: FreeBSD and LGPL, see license.* for more details.
"""
# Support for Python 2.7
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *
from future.utils import iteritems

import warnings

from lxml import etree
from datetime import datetime
import dateutil.parser
import dateutil.tz

from podgen.warnings import NotSupportedByItunesWarning
from podgen.util import formatRFC2822, listToHumanreadableStr
from podgen.constants import EPISODE_TYPE_FULL, EPISODE_TYPE_TRAILER, EPISODE_TYPE_BONUS
from podgen.compat import string_types

from .transcript import Transcript
from .location import Location


class Episode(object):
    """Class representing an episode in a podcast. Corresponds to an RSS Item.

    When creating a new Episode, you can populate any attribute
    using keyword arguments. Use the attribute's name on the left side of
    the equals sign and its value on the right side. Here's an example::

        >>> # This...
        >>> ep = Episode()
        >>> ep.title = "Exploring the RTS genre"
        >>> ep.summary = "Tory and I talk about a genre of games we've " + \\
        ...              "never dared try out before now..."
        >>> # ...is equal to this:
        >>> ep = Episode(
        ...    title="Exploring the RTS genre",
        ...    summary="Tory and I talk about a genre of games we've "
        ...            "never dared try out before now..."
        ... )

    :raises: TypeError if you try to set an attribute which doesn't exist,
             ValueError if you set an attribute to an invalid value.

    You must have filled in either :attr:`.title` or :attr:`.summary` before
    the RSS can be generated.

    To add an episode to a podcast::

        >>> import podgen
        >>> p = podgen.Podcast()
        >>> episode = podgen.Episode()
        >>> p.episodes.append(episode)

    You may also replace the last two lines with a shortcut::

        >>> episode = p.add_episode(podgen.Episode())


    .. seealso::

       :doc:`/usage_guide/episodes`
          A friendlier introduction to episodes.
    """

    def __init__(self, **kwargs):
        # RSS
        self.__authors = []
        self.summary = None
        """The summary of this episode, in a format that can be parsed by
        XHTML parsers.

        If your summary isn't fit to be parsed as XHTML, you can use
        :py:func:`podgen.htmlencode` to fix the text, like this::

            >>> ep.summary = podgen.htmlencode("We spread lots of love <3")
            >>> ep.summary
            We spread lots of love &lt;3

        In iTunes, the summary is shown in a separate window that appears when
        the "circled i" in the Description column is clicked. This field can be
        up to 4000 characters in length.

        See also :py:attr:`.Episode.subtitle` and
        :py:attr:`.Episode.long_summary`.

        :type: :obj:`str` which can be parsed as XHTML.
        :RSS: description"""

        self.long_summary = None
        """A long (read: full) summary, which supplements the shorter
        :attr:`~podgen.Episode.summary`. Like summary, this must be compatible
        with XHTML parsers; use :func:`podgen.htmlencode` if this isn't HTML.

        This attribute should be seen as a full, longer variation of
        summary if summary exists. Even then, the long_summary should be
        independent from summary, in that you only need to read one of them.
        This means you may have to repeat the first sentences.

        :type: :obj:`str` which can be parsed as XHTML.
        :RSS: content:encoded or description
        """

        self.__media = None

        self.id = None
        """This episode's globally unique identifier.

        If not present, the URL of the enclosed media is used. This is usually
        the best way to go, **as long as the media URL doesn't change**.

        Set the id to boolean ``False`` if you don't want to associate any id to
        this episode.

        It is important that an episode keeps the same ID until the end of time,
        since the ID is used by clients to identify which episodes have been
        listened to, which episodes are new, and so on. Changing the ID causes
        the same consequences as deleting the existing episode and adding a
        new, identical episode.

        Note that this is a GLOBALLY unique identifier. Thus, not only must it
        be unique in this podcast, it must not be the same ID as any other
        episode for any podcast out there. To ensure this, you should use a
        domain which you own (for example, use something like
        http://example.org/podcast/episode1 if you own example.org).

        :type: :obj:`str`, :obj:`None` to use default or :obj:`False` to leave
            out.
        :RSS: guid
        """

        self.link = None
        """The link to the full version of this episode's :attr:`.summary`.
        Remember to start the link with the scheme, e.g. https://.

        :type: :obj:`str`
        :RSS: link
        """

        self.__publication_date = None

        self.title = None
        """This episode's human-readable title.
        Title is mandatory and should not be blank.

        :type: :obj:`str`
        :RSS: title
        """

        # ITunes tags
        # http://www.apple.com/itunes/podcasts/specs.html#rss
        self.__withhold_from_itunes = False

        self.__image = None

        self.__itunes_duration = None

        self.__explicit = None

        self.is_closed_captioned = False
        """Whether this podcast includes a video episode with embedded `closed
        captioning`_ support. Defaults to ``False``.

        :type: :obj:`bool`
        :RSS: itunes:isClosedCaptioned

        .. _closed captioning: https://en.wikipedia.org/wiki/Closed_captioning
        """

        self.__position = None

        self.__episode_number = None

        self.__season = None

        self.__episode_type = EPISODE_TYPE_FULL

        self.subtitle = None
        """A short subtitle.

        This is shown in the Description column in iTunes.
        The subtitle displays best if it is only a few words long.

        :type: :obj:`str`
        :RSS: itunes:subtitle
        """

        self.__transcripts = []
        """List of episode transcript links.
        
        The transcript tag exists in the podcast namespace
        https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md#transcript
        https://podcastindex.org/namespace/1.0
        """

        self.__location = None
        """The location of the episode.

        See https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md#location
        for an overview of the location tag

       :type: :obj:`podgen.Location`
        """

        # It is time to assign the keyword arguments
        for attribute, value in iteritems(kwargs):
            if hasattr(self, attribute):
                setattr(self, attribute, value)
            else:
                raise TypeError("Keyword argument %s (with value %s) not "
                                "recognized!" % (attribute, value))

    def rss_entry(self):
        """Create an RSS item using lxml's etree and return it.

        This is primarily used by :class:`podgen.Podcast` when generating the
        podcast's RSS feed.

        :returns: etree.Element('item')
        """

        ITUNES_NS = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
        DUBLIN_NS = 'http://purl.org/dc/elements/1.1/'
        PODCAST_NS = 'https://podcastindex.org/namespace/1.0'

        entry = etree.Element('item')

        if not (self.title or self.summary):
            raise ValueError('Required fields not set, make sure either '
                             'title or summary is set!')

        if self.title:
            title = etree.SubElement(entry, 'title')
            title.text = self.title

        if self.link:
            link = etree.SubElement(entry, 'link')
            link.text = self.link

        if self.summary or self.long_summary:
            if self.summary and self.long_summary:
                # Both are present, so use both content and description
                description = etree.SubElement(entry, 'description')
                description.text = etree.CDATA(self.summary)
                content = etree.SubElement(entry, '{%s}encoded' %
                                     'http://purl.org/rss/1.0/modules/content/')
                content.text = etree.CDATA(self.long_summary)
            else:
                # Only one is present, use description because of support
                description = etree.SubElement(entry, 'description')
                description.text = \
                    etree.CDATA(self.summary or self.long_summary)

        if self.__authors:
            authors_with_name = [a.name for a in self.__authors if a.name]
            if authors_with_name:
                # We have something to display as itunes:author, combine all
                # names
                itunes_author = \
                    etree.SubElement(entry, '{%s}author' % ITUNES_NS)
                itunes_author.text = listToHumanreadableStr(authors_with_name)
            if len(self.__authors) > 1 or not self.__authors[0].email:
                # Use dc:creator, since it supports multiple authors (and
                # author without email)
                for a in self.__authors or []:
                    author = etree.SubElement(entry, '{%s}creator' % DUBLIN_NS)
                    if a.name and a.email:
                        author.text = "%s <%s>" % (a.name, a.email)
                    elif a.name:
                        author.text = a.name
                    else:
                        author.text = a.email
            else:
                # Only one author and with email, so use rss author
                author = etree.SubElement(entry, 'author')
                author.text = str(self.__authors[0])

        if self.id:
            rss_guid = self.id
        elif self.__media and self.id is None:
            rss_guid = self.__media.url
        else:
            # self.__rss_guid was set to boolean False, or no enclosure
            rss_guid = None
        if rss_guid:
            guid = etree.SubElement(entry, 'guid')
            guid.text = rss_guid
            guid.attrib['isPermaLink'] = 'false'

        if self.__media:
            enclosure = etree.SubElement(entry, 'enclosure')
            enclosure.attrib['url'] = self.__media.url
            enclosure.attrib['length'] = str(self.__media.size)
            enclosure.attrib['type'] = self.__media.type

            if self.__media.duration:
                duration = etree.SubElement(entry, '{%s}duration' % ITUNES_NS)
                duration.text = self.__media.duration_str

        if self.__publication_date:
            pubDate = etree.SubElement(entry, 'pubDate')
            pubDate.text = formatRFC2822(self.__publication_date)

        if self.__withhold_from_itunes:
            # It is True, so include element - otherwise, don't include it
            block = etree.SubElement(entry, '{%s}block' % ITUNES_NS)
            block.text = 'Yes'

        if self.__image:
            image = etree.SubElement(entry, '{%s}image' % ITUNES_NS)
            image.attrib['href'] = self.__image

        if self.__explicit is not None:
            explicit = etree.SubElement(entry, '{%s}explicit' % ITUNES_NS)
            explicit.text = "Yes" if self.__explicit else "No"

        if self.is_closed_captioned:
            is_closed_captioned = etree.SubElement(entry,
                                            '{%s}isClosedCaptioned' % ITUNES_NS)
            is_closed_captioned.text = 'Yes'

        if self.__episode_type != EPISODE_TYPE_FULL:
            episode_type = etree.SubElement(
                entry,
                '{%s}episodeType' % ITUNES_NS
            )
            episode_type.text = self.__episode_type

        if self.__season is not None:
            season = etree.SubElement(
                entry,
                '{%s}season' % ITUNES_NS
            )
            season.text = str(self.__season)

        if self.__position is not None and self.__position >= 0:
            order = etree.SubElement(entry, '{%s}order' % ITUNES_NS)
            order.text = str(self.__position)

        if self.__episode_number is not None:
            episode_number = etree.SubElement(entry, '{%s}episode' % ITUNES_NS)
            # Convert via int, since we stored the original as-is
            episode_number.text = str(int(self.__episode_number))

        if self.subtitle:
            subtitle = etree.SubElement(entry, '{%s}subtitle' % ITUNES_NS)
            subtitle.text = self.subtitle

        if self.transcripts:
            for transcript in self.transcripts:
                transcriptElem = etree.SubElement(entry, '{%s}transcript' % PODCAST_NS)
                transcriptElem.attrib['url'] = transcript.url
                transcriptElem.attrib['type'] = transcript.type
                if transcript.language:
                    transcriptElem.attrib['language'] = transcript.language
                if transcript.is_caption:
                    transcriptElem.attrib['rel'] = "captions"

        if self.location:
            locationElem = self.location.rss_entry()
            entry.append(locationElem)

        return entry

    @property
    def authors(self):
        """List of :class:`~podgen.Person` that contributed to this
        episode.

        The authors don't need to have both name and email set. They're usually
        not displayed anywhere.

        .. note::

            You do not need to provide any authors for an episode if
            they're identical to the podcast's authors.

        Any value you assign to authors will be automatically converted to a
        list, but only if it's iterable (like tuple, set and so on). It is an
        error to assign a single :class:`~podgen.Person` object to this
        attribute::

            >>> # This results in an error
            >>> ep.authors = Person("John Doe", "johndoe@example.org")
            TypeError: Only iterable types can be assigned to authors, ...
            >>> # This is the correct way:
            >>> ep.authors = [Person("John Doe", "johndoe@example.org")]

        The initial value is an empty list, so you can use the list methods
        right away.

        Example::

            >>> # This attribute is just a list - you can for example append:
            >>> ep.authors.append(Person("John Doe", "johndoe@example.org"))
            >>> # Or assign a new list (discarding earlier authors)
            >>> ep.authors = [Person("John Doe", "johndoe@example.org"),
            ...               Person("Mary Sue", "marysue@example.org")]

        :type: :obj:`list` of :class:`podgen.Person`
        :RSS: author or dc:creator, and itunes:author
        """
        return self.__authors

    @authors.setter
    def authors(self, authors):
        try:
            self.__authors = list(authors)
        except TypeError:
            raise TypeError("Only iterable types can be assigned to authors, "
                            "%s given. You must put your object in a list, "
                            "even if there's only one author." % authors)

    @property
    def publication_date(self):
        """The time and date this episode was first published.

        The value can be a :obj:`str`, which will be parsed and
        made into a :class:`datetime.datetime` object when assigned. You may
        also assign a :class:`datetime.datetime` object directly. In both cases,
        you must ensure that the value includes timezone information.

        :type: :obj:`str` (will be converted to and stored as
            :class:`datetime.datetime`) or :class:`datetime.datetime`.
        :RSS: pubDate

        .. note::

           Don't use the media file's modification date as the publication
           date, unless they're the same. It looks very odd when an episode
           suddenly pops up in the feed, but it claims to be several hours old!
        """
        return self.__publication_date

    @publication_date.setter
    def publication_date(self, publication_date):
        if publication_date is not None:
            if isinstance(publication_date, string_types):
                publication_date = dateutil.parser.parse(publication_date)
            if not isinstance(publication_date, datetime):
                raise ValueError('Invalid datetime format')
            if publication_date.tzinfo is None:
                raise ValueError('Datetime object has no timezone info')
            self.__publication_date = publication_date
        else:
            self.__publication_date = None

    @property
    def media(self):
        """Get or set the :class:`~podgen.Media` object that is attached
        to this episode.

        Note that if :py:attr:`.id` is not set, the media's URL is used as
        the id. If you rely on this, you should make sure the URL never changes,
        since changing the id messes up with clients (they will think this
        episode is new again, even if the user has listened to it already).
        Therefore, you should only rely on this behaviour if you own the domain
        which the episodes reside on. If you don't, then you must set
        :py:attr:`.id` to an appropriate value manually.

        :type: :class:`podgen.Media`
        :RSS: enclosure and itunes:duration
        """
        return self.__media

    @media.setter
    def media(self, media):
        if media is not None:
            # Test that the media quacks like a duck
            if hasattr(media, "url") and hasattr(media, "size") and \
               hasattr(media, "type"):
                # It's a duck
                self.__media = media
            else:
                raise TypeError("The parameter media must have the attributes "
                                "url, size and type.")
        else:
            self.__media = None

    @property
    def withhold_from_itunes(self):
        """Prevent this episode from appearing in the iTunes podcast directory.
        Note that the episode can still be found by inspecting the XML, so it is
        still public.

        One use case would be if you knew that this episode would get you kicked
        out from iTunes, should it make it there. In such cases, you can set
        withhold_from_itunes to ``True`` so this episode isn't published on
        iTunes, allowing you to publish it to everyone else while keeping your
        podcast on iTunes.

        This attribute defaults to ``False``, of course.

        :type: :obj:`bool`
        :RSS: itunes:block
        """
        return self.__withhold_from_itunes

    @withhold_from_itunes.setter
    def withhold_from_itunes(self, withhold_from_itunes):
        if withhold_from_itunes is not None:
            if withhold_from_itunes is True or withhold_from_itunes is False:
                self.__withhold_from_itunes = withhold_from_itunes
            else:
                raise TypeError("withhold_from_itunes expects bool or None, "
                                "got %s" % withhold_from_itunes)
        else:
            self.__withhold_from_itunes = None

    @property
    def image(self):
        """The podcast episode's image, overriding the podcast's
        :attr:`~.Podcast.image`.

        This attribute specifies the absolute URL to the artwork for your
        podcast. iTunes prefers square images that are at least ``1400x1400``
        pixels.

        iTunes supports images in JPEG and PNG formats with an RGB color space
        (CMYK is not supported). The URL must end in ".jpg" or ".png"; a
        :class:`.NotSupportedByItunesWarning` will be issued if it doesn't.

        :type: :obj:`str`
        :RSS: itunes:image

        .. note::

           If you change an episode’s image, you should also change the file’s
           name; iTunes doesn't check the actual file to see if it's changed.

           Additionally, the server hosting your cover art image must allow HTTP
           HEAD requests.

        .. warning::

            Almost no podcatchers support this. iTunes supports it only if you
            embed the cover in the media file (the same way you would embed
            an album cover), and recommends that you use Garageband's Enhanced
            Podcast feature.

            The podcast's image is used if this isn't supported.
        """
        return self.__image

    @image.setter
    def image(self, image):
        if image is not None:
            lowercase_image = str(image).lower()
            if not (lowercase_image.endswith(('.jpg', '.jpeg', '.png'))):
                warnings.warn('Image filename must end with png or jpg, not '
                      '%s' % image.split(".")[-1], NotSupportedByItunesWarning,
                      stacklevel=2)
            self.__image = image
        else:
            self.__image = None

    @property
    def explicit(self):
        """Whether this podcast episode contains material which may be
        inappropriate for children.

        The value of the podcast's explicit attribute is used by default, if
        this is kept as ``None``.

        If you set this to ``True``, an "explicit" parental advisory
        graphic will appear in the Name column in iTunes. If the value is
        ``False``, the parental advisory type is considered Clean, meaning that
        no explicit language or adult content is included anywhere in this
        episode, and a "clean" graphic will appear.

        :type: :obj:`bool`
        :RSS: itunes:explicit
        """
        return self.__explicit

    @explicit.setter
    def explicit(self, explicit):
        if explicit is not None:
            # Force explicit to be bool, so no one uses "no" and expects False
            if explicit not in (True, False):
                raise ValueError('Invalid value "%s" for explicit tag'
                                 % explicit)
            self.__explicit = explicit
        else:
            self.__explicit = None

    @property
    def episode_type(self):
        """Indicate whether this is a full episode, or a bonus or trailer for
        an episode or a season.

        By default, the episode is taken to be a full episode.

        Use the constants ``EPISODE_TYPE_FULL``, ``EPISODE_TYPE_TRAILER`` or
        ``EPISODE_TYPE_BONUS`` (available to import from ``podgen``).

        :type: One of the three constants mentioned.
        :RSS: itunes:episodeType
        """
        return self.__episode_type

    @episode_type.setter
    def episode_type(self, episode_type):
        as_str = str(episode_type)
        if (as_str not in (
            EPISODE_TYPE_FULL,
            EPISODE_TYPE_BONUS,
            EPISODE_TYPE_TRAILER,
        )):
            raise ValueError('Invalid episode_type value "%s"' % as_str)

        self.__episode_type = as_str

    @property
    def season(self):
        """The number of the season this episode belongs to.

        By default, the episode belongs to no season, indicated by this
        attribute being set to :obj:`None`.

        Some podcast applications may choose to show season numbers only when
        there is more than one season.

        :type: :obj:`None` or positive :obj:`int`
        :RSS: itunes:season
        """
        return self.__season

    @season.setter
    def season(self, season):
        if season is None:
            self.__season = None
        else:
            as_int = int(season)
            if as_int <= 0:
                raise ValueError('Season number must be a positive, non-zero '
                                'integer; not "%s"' % as_int)
            self.__season = as_int

    @property
    def position(self):
        """A custom position for this episode on the iTunes store page.

        If you would like this episode to appear first, set it to ``1``.
        If you want it second, set it to ``2``, and so on. If multiple episodes
        share the same position, they will be sorted by their
        :attr:`publication date <.Episode.publication_date>`.

        To remove the order from the episode, set the position back to
        :obj:`None`.

        :type: :obj:`int`
        :RSS: itunes:order
        """
        return self.__position

    @position.setter
    def position(self, position):
        if position is not None:
            self.__position = int(position)
        else:
            self.__position = None

    @property
    def episode_number(self):
        """This episode's number (within the season).

        This number is used to sort the episodes for
        :attr:`serial podcasts <.Podcast.is_serial>`. It can also be displayed
        to the user as the episode number. For
        :attr:`full episodes <episode_type>`, the episode numbers
        should be unique within each season.

        This is mandatory for full episodes of serial podcasts.

        :type: :obj:`None` or positive :obj:`int`
        :RSS: itunes:episode
        """
        return self.__episode_number

    @episode_number.setter
    def episode_number(self, episode_number):
        if episode_number is not None:
            as_integer = int(episode_number)
            if 0 < as_integer:
                # Store original (not int), to avoid confusion when setting
                self.__episode_number = episode_number
            else:
                raise ValueError(
                    'episode_number must be a positive, non-zero integer; not '
                    '"%s"' % episode_number
                )
        else:
            self.__episode_number = None

    @property
    def transcripts(self):
        """List of :class: `podgen.Transcript` objects that
        contains the episode transcriptions data.

         See :py:meth:`.add_transcript` for an easy way to create new transcripts and
        assign them to this episode in one call.

        :type: :obj:`list` of :class:`podgen.Transcript`
        :RSS: item child elements
        """
        return self.__transcripts

    @transcripts.setter
    def transcripts(self, transcripts):
        # Ensure it is a list of transcripts or empty list
        if transcripts is None:
            transcripts = []

        try:
            transcripts = list(transcripts)
        except:
            raise TypeError("Expected an iterable of transcripts, got %r" % transcripts)

        for transcript in transcripts:
            if not isinstance(transcript, Transcript):
                raise TypeError("A Transcript object must be used, got "
                                "%r" % transcript)

        self.__transcripts = transcripts

    def add_transcript(self, new_transcript):
        """Shorthand method which adds a new transcript to the episode.
        The transcript object must be passed as a parameter to make sure
        all the required parameters are specified and valid.
        This is the easiest way to add a transcript to an episode.

        :param new_transcript: :class:`.Transcript` object to add.
        :returns: Transcript object passed to this function.

        Example::

            >>> import podgen
            >>> transcript = Transcript("https://examples.com/transcript_sample.txt", "text/html")
            >>> # adding the transcript to the podcast object p
            >>> p.add_episode(transcript)

        Internally, this method creates a new instance of
        :attr:`~podgen.Transcript`, which means you can change what
        """
        self.transcripts.append(new_transcript)
        return new_transcript

    @property
    def location(self):
        """Object of :class:`~podgen.Location` with data about the episode location

        The location helps into parsing coordinaes and geo uri::

            >>> e.location = Location("Austin, TX", osm="R113314")
            >>> e.location.text
            'Austin, TX'
            >>> e.location.osm
            'R113314'
            >>> e.location.latitude = 30.2672
            >>> e.location.longitude = 97.7431
            >>> e.location.geo
            'geo:30.2672,97.7431'

        :type: :obj:`podgen.Location`
        """
        return self.__location

    @location.setter
    def location(self, location):
        if location is None:
            self.__location = None
        else:
            if not isinstance(location, Location):
                raise ValueError("Location attribute must be a podgen.Location object."
                                 "Received %r instead" % location)
            else:
                self.__location = location

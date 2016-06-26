# -*- coding: utf-8 -*-
"""
    feedgen.entry
    ~~~~~~~~~~~~~

    :copyright: 2013, Lars Kiesow <lkiesow@uos.de>

    :license: FreeBSD and LGPL, see license.* for more details.
"""
import collections

from lxml import etree
from datetime import datetime
import dateutil.parser
import dateutil.tz
from feedgen.util import ensure_format, formatRFC2822, htmlencode
from feedgen.compat import string_types
from builtins import str


class BaseEpisode(object):
    """Class representing an episode in a podcast. Corresponds to an RSS Item.

    Its name indicates that this is the superclass for all episode classes.
    It is not meant to indicate that this class misses functionality; in 99%
    of all cases, this class is the right one to use for episodes.
    """

    def __init__(self):
        # RSS
        self.__rss_author      = None
        self.__rss_content     = None
        self.__rss_enclosure   = None
        self.__rss_guid        = None
        self.__rss_link        = None
        self.__rss_pubDate     = None
        self.__rss_title       = None

        # ITunes tags
        # http://www.apple.com/itunes/podcasts/specs.html#rss
        self.__itunes_author = None
        self.__itunes_block = None
        self.__itunes_image = None
        self.__itunes_duration = None
        self.__itunes_explicit = None
        self.__itunes_is_closed_captioned = None
        self.__itunes_order = None
        self.__itunes_subtitle = None


    def rss_entry(self, extensions=True):
        """Create a RSS item and return it."""
        entry = etree.Element('item')

        if not ( self.__rss_title or self.__rss_content):
            raise ValueError('Required fields not set')

        if self.__rss_title:
            title = etree.SubElement(entry, 'title')
            title.text = self.__rss_title

        if self.__rss_link:
            link = etree.SubElement(entry, 'link')
            link.text = self.__rss_link

        if self.__rss_content:
            description = etree.SubElement(entry, 'description')
            description.text = etree.CDATA(self.__rss_content)
            content = etree.SubElement(entry, '{%s}encoded' %
                                    'http://purl.org/rss/1.0/modules/content/')
            content.text = etree.CDATA(self.__rss_content)
        for a in self.__rss_author or []:
            author = etree.SubElement(entry, 'author')
            author.text = a

        if self.__rss_guid:
            rss_guid = self.__rss_guid
        elif self.__rss_enclosure and self.__rss_guid is None:
            rss_guid = self.__rss_enclosure['url']
        else:
            # self.__rss_guid was set to boolean False, or no enclosure
            rss_guid = None
        if rss_guid:
            guid = etree.SubElement(entry, 'guid')
            guid.text = rss_guid
            guid.attrib['isPermaLink'] = 'false'

        if self.__rss_enclosure:
            enclosure = etree.SubElement(entry, 'enclosure')
            enclosure.attrib['url'] = self.__rss_enclosure['url']
            enclosure.attrib['length'] = str(self.__rss_enclosure['length'])
            enclosure.attrib['type'] = self.__rss_enclosure['type']

        if self.__rss_pubDate:
            pubDate = etree.SubElement(entry, 'pubDate')
            pubDate.text = formatRFC2822(self.__rss_pubDate)

        # Itunes fields
        ITUNES_NS = 'http://www.itunes.com/dtds/podcast-1.0.dtd'

        if self.__itunes_author:
            author = etree.SubElement(entry, '{%s}author' % ITUNES_NS)
            author.text = self.__itunes_author

        if not self.__itunes_block is None:
            block = etree.SubElement(entry, '{%s}block' % ITUNES_NS)
            block.text = 'yes' if self.__itunes_block else 'no'

        if self.__itunes_image:
            image = etree.SubElement(entry, '{%s}image' % ITUNES_NS)
            image.attrib['href'] = self.__itunes_image

        if self.__itunes_duration:
            duration = etree.SubElement(entry, '{%s}duration' % ITUNES_NS)
            duration.text = self.__itunes_duration

        if self.__itunes_explicit in ('yes', 'no', 'clean'):
            explicit = etree.SubElement(entry, '{%s}explicit' % ITUNES_NS)
            explicit.text = self.__itunes_explicit

        if not self.__itunes_is_closed_captioned is None:
            is_closed_captioned = etree.SubElement(entry, '{%s}isClosedCaptioned' % ITUNES_NS)
            is_closed_captioned.text = 'yes' if self.__itunes_is_closed_captioned else 'no'

        if not self.__itunes_order is None and self.__itunes_order >= 0:
            order = etree.SubElement(entry, '{%s}order' % ITUNES_NS)
            order.text = str(self.__itunes_order)

        if self.__itunes_subtitle:
            subtitle = etree.SubElement(entry, '{%s}subtitle' % ITUNES_NS)
            subtitle.text = self.__itunes_subtitle

        return entry



    def title(self, title=None):
        """Get or set the title value of the entry. It should contain a human
        readable title for the entry. Title is mandatory and should not be blank.

        :param title: The new title of the entry.
        :returns: The entriess title.
        """
        if not title is None:
            self.__rss_title = title
        return self.__rss_title


    def id(self, new_id=None):
        """Get or set this episode's globally unique identifier.

        If not present, the URL of the enclosed media is used. Set the id to
        boolean False to suppress this behaviour.

        It is important that an episode keeps the same ID until the end of time,
        since the ID is used by clients to identify which episodes have been
        listened to, which episodes are new, and so on. Changing the ID causes
        the same consequences as deleting the existing episode and adding a
        new, identical episode.

        Note that this is a GLOBALLY unique identifier. Thus, not only must it
        be unique in this podcast, it must not be the same ID as any other
        episode for any podcast out there. To ensure this, you should use a
        domain which you own (for example, use something like
        http://example.org/podcast/episode1.mp3 if you own example.org).

        This property corresponds to the RSS GUID element.

        :param new_id: Globally unique, permanent id of this episode.
        :returns: Id of this episode.
        """
        if not new_id is None:
            self.__rss_guid = new_id
        return self.__rss_guid


    def author(self, author=None, replace=False, **kwargs):
        """Get or set autor data. An author element is a dict containing a name and
        an email adress. Email is mandatory.

        This method can be called with:
        - the fields of an author as keyword arguments
        - the fields of an author as a dictionary
        - a list of dictionaries containing the author fields

        An author has the following fields:
        - *name* conveys a human-readable name for the person.
        - *email* contains an email address for the person.

        :param author:  Dict or list of dicts with author data.
        :param replace: Add or replace old data.

        Example::

            >>> author( { 'name':'John Doe', 'email':'jdoe@example.com' } )
            [{'name':'John Doe','email':'jdoe@example.com'}]

            >>> author([{'name':'Mr. X'},{'name':'Max'}])
            [{'name':'John Doe','email':'jdoe@example.com'},
                    {'name':'John Doe'}, {'name':'Max'}]

            >>> author( name='John Doe', email='jdoe@example.com', replace=True )
            [{'name':'John Doe','email':'jdoe@example.com'}]

        """
        if author is None and kwargs:
            author = kwargs
        if not author is None:
            if replace or self.__rss_author is None:
                self.__rss_author = []
            authors = ensure_format( author,
                    set(['name', 'email']), set(['email']))
            self.__rss_author += ['%s (%s)' % ( a['email'], a['name'] ) for a in authors]
        return self.__rss_author


    def summary(self, new_summary=None, html=True):
        """Get or set the summary of this episode.

        In iTunes, the summary is shown in a separate window that appears when
        the "circled i" in the Description column is clicked. This field can be
        up to 4000 characters in length.

        See also :py:meth:`.itunes_subtitle`.

        :param new_summary: The summary of this episode.
        :param html: Treat the summary as HTML. If set to False, the summary
            will be HTML escaped (thus, any tags will be displayed in plain
            text). If set to True, the tags are parsed by clients which support
            HTML, but if something is not to be regarded as HTML, you must
            escape it yourself using HTML entities.
        :returns: Summary of this episode.
        """
        if not new_summary is None:
            if not html:
                new_summary = htmlencode(new_summary)
            self.__rss_content = new_summary
        return self.__rss_content


    def link(self, href=None):
        """Get or set the link to the full version of this episode description.

        :param href: the URI of the referenced resource (typically a Web page)
        :returns: The current link URI.
        """
        if not href is None:
            self.__rss_link = href
        return self.__rss_link


    def published(self, published=None):
        """Set or get the published value which contains the time of the initial
        creation or first availability of the entry.

        The value can either be a string which will automatically be parsed or a
        datetime.datetime object. In any case it is necessary that the value
        include timezone information.

        :param published: The creation date.
        :returns: Creation date as datetime.datetime
        """
        if not published is None:
            if isinstance(published, string_types):
                published = dateutil.parser.parse(published)
            if not isinstance(published, datetime):
                raise ValueError('Invalid datetime format')
            if published.tzinfo is None:
                raise ValueError('Datetime object has no timezone info')
            self.__rss_pubDate = published

        return self.__rss_pubDate


    def enclosure(self, url=None, length=None, type=None):
        """Get or set the value of enclosure which describes a media object that
        is attached to this item.

        Note that if :py:meth:`.id` is not set, the enclosure's url is used as
        the globally unique identifier. If you rely on this, you should make
        sure the url never changes, since changing the id messes up with clients
        (they will think this episode is new again, even if the user already
        has listened to it). Therefore, you should only rely on this behaviour
        if you own the domain which the episodes reside on. If you don't, then
        you must set :py:meth:`.id` to something which is unique not only for
        this podcast, but for all podcasts.

        :param url: URL of the media object.
        :param length: Size of the media in bytes.
        :param type: Mimetype of the linked media.
        :returns: Data of the enclosure element.
        """
        if not url is None:
            self.__rss_enclosure = {'url': url, 'length': length, 'type': type}
        return self.__rss_enclosure

    def itunes_author(self, itunes_author=None):
        """Get or set the itunes:author of the podcast episode. The content of
        this tag is shown in the Artist column in iTunes. If the tag is not
        present, iTunes uses the contents of the <author> tag. If <itunes:author>
        is not present at the feed level, iTunes will use the contents of
        <managingEditor>.

        :param itunes_author: The author of the podcast.
        :type itunes_author: str
        :returns: The author of the podcast.
        """
        if not itunes_author is None:
            self.__itunes_author = itunes_author
        return self.__itunes_author

    def itunes_block(self, itunes_block=None):
        """Get or set the ITunes block attribute. Use this to prevent episodes
        from appearing in the iTunes podcast directory. Note that the episode can still be
        found by inspecting the XML, thus it is public.

        :param itunes_block: Block podcast episodes.
        :type itunes_block: bool
        :returns: If the podcast episode is blocked.
        """
        if not itunes_block is None:
            self.__itunes_block = itunes_block
        return self.__itunes_block

    def itunes_image(self, itunes_image=None):
        """Get or set the image for the podcast episode. This tag specifies the
        artwork for your podcast. Put the URL to the image in the href attribute.
        iTunes prefers square .jpg images that are at least 1400x1400 pixels,
        which is different from what is specified for the standard RSS image tag.
        In order for a podcast to be eligible for an iTunes Store feature, the
        accompanying image must be at least 1400x1400 pixels.

        iTunes supports images in JPEG and PNG formats with an RGB color space
        (CMYK is not supported). The URL must end in ".jpg" or ".png". If the
        <itunes:image> tag is not present, iTunes will use the contents of the
        RSS image tag.

        If you change your podcast’s image, also change the file’s name. iTunes
        may not change the image if it checks your feed and the image URL is the
        same. The server hosting your cover art image must allow HTTP head
        requests for iTS to be able to automatically update your cover art.

        :param itunes_image: Image of the podcast.
        :type itunes_image: str
        :returns: Image of the podcast.
        """
        if not itunes_image is None:
            lowercase_itunes_image = itunes_image.lower()
            if not (lowercase_itunes_image.endswith(('.jpg', '.jpeg', '.png'))):
                raise ValueError('Image filename must end with png or jpg, not .%s' % itunes_image.split(".")[-1])
            self.__itunes_image = itunes_image
        return self.__itunes_image

    def itunes_duration(self, itunes_duration=None):
        """Get or set the duration of the podcast episode. The content of this
        tag is shown in the Time column in iTunes.

        The tag can be formatted HH:MM:SS, H:MM:SS, MM:SS, or M:SS (H = hours,
        M = minutes, S = seconds). If an integer is provided (no colon present),
        the value is assumed to be in seconds. If one colon is present, the
        number to the left is assumed to be minutes, and the number to the right
        is assumed to be seconds. If more than two colons are present, the
        numbers farthest to the right are ignored.

        :param itunes_duration: Duration of the podcast episode.
        :type itunes_duration: str or int
        :returns: Duration of the podcast episode.
        """
        if not itunes_duration is None:
            itunes_duration = str(itunes_duration)
            if len(itunes_duration.split(':')) > 3 or \
                            itunes_duration.lstrip('0123456789:') != '':
                ValueError('Invalid duration format "%s"' % itunes_duration)
            self.__itunes_duration = itunes_duration
        return self.itunes_duration

    def itunes_explicit(self, itunes_explicit=None):
        """Get or the the itunes:explicit value of the podcast episode. This tag
        should be used to indicate whether your podcast episode contains explicit
        material. The three values for this tag are "yes", "no", and "clean".

        If you populate this tag with "yes", an "explicit" parental advisory
        graphic will appear next to your podcast artwork on the iTunes Store and
        in the Name column in iTunes. If the value is "clean", the parental
        advisory type is considered Clean, meaning that no explicit language or
        adult content is included anywhere in the episodes, and a "clean" graphic
        will appear. If the explicit tag is present and has any other value
        (e.g., "no"), you see no indicator — blank is the default advisory type.

        :param itunes_explicit: "yes" if the podcast contains explicit material, "clean" if it doesn't. "no" counts
            as blank.
        :type itunes_explicit: str
        :returns: If the podcast episode contains explicit material.
        """
        if not itunes_explicit is None:
            if not itunes_explicit in ('', 'yes', 'no', 'clean'):
                raise ValueError('Invalid value "%s" for explicit tag' % itunes_explicit)
            self.__itunes_explicit = itunes_explicit
        return self.__itunes_explicit

    def itunes_is_closed_captioned(self, itunes_is_closed_captioned=None):
        """Get or set the is_closed_captioned value of the podcast episode. This
        tag should be used if your podcast includes a video episode with embedded
        closed captioning support. The two values for this tag are "yes" and
        "no”.

        :param itunes_is_closed_captioned: If the episode has closed captioning support.
        :type itunes_is_closed_captioned: bool or str
        :returns: If the episode has closed captioning support.
        """
        if not itunes_is_closed_captioned is None:
            self.__itunes_is_closed_captioned = itunes_is_closed_captioned in ('yes', True)
        return self.__itunes_is_closed_captioned

    def itunes_order(self, itunes_order=None):
        """Get or set the itunes:order value of the podcast episode. This tag can
        be used to override the default ordering of episodes on the store.

        This tag is used at an <item> level by populating with the number value
        in which you would like the episode to appear on the store. For example,
        if you would like an <item> to appear as the first episode in the
        podcast, you would populate the <itunes:order> tag with “1”. If
        conflicting order values are present in multiple episodes, the store will
        use default ordering (pubDate).

        To remove the order from the episode set the order to a value below zero.

        :param itunes_order: The order of the episode.
        :type itunes_order: int
        :returns: The order of the episode.
        """
        if not itunes_order is None:
            self.__itunes_order = int(itunes_order)
        return self.__itunes_order

    def itunes_subtitle(self, itunes_subtitle=None):
        """Get or set the itunes:subtitle value for the podcast episode. The
        contents of this tag are shown in the Description column in iTunes. The
        subtitle displays best if it is only a few words long.

        :param itunes_subtitle: Subtitle of the podcast episode.
        :type itunes_subtitle: str
        :returns: Subtitle of the podcast episode.
        """
        if not itunes_subtitle is None:
            self.__itunes_subtitle = itunes_subtitle
        return self.__itunes_subtitle
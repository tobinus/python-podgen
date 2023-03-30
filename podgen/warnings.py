# -*- coding: utf-8 -*-
"""
    podgen.warnings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This file contains PodGen-specific warnings.
    They can be imported directly from ``podgen``.

    :copyright: 2019, Thorben Dahl <thorben@sjostrom.no>
    :license: FreeBSD and LGPL, see license.* for more details.
"""
# Support for Python 2.7
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *


class PodgenWarning(UserWarning):
    """
    Superclass for all warnings defined by PodGen.
    """
    pass


class NotRecommendedWarning(PodgenWarning):
    """
    Warns against behaviour or usage which is usually discouraged. However,
    there may exist exceptions where there is no better way.
    """
    pass


class LegacyCategoryWarning(PodgenWarning):
    """
    Indicates that the categories created is an old categories. It will still be
    accepted by Apple Podcasts, but it would be wise to use the new categories
    since they may have more relevant options for your podcast.

    .. seealso::

       `What's New: Enhanced Apple Podcasts Categories <https://itunespartner.apple.com/podcasts/whats-new/100002564>`_
          Consequences of using old categories.

       `Podcasts Connect Help: Apple Podcasts categories <https://help.apple.com/itc/podcasts_connect/#/itc9267a2f12>`_
          Up-to-date list of available categories.

       `Podnews: New and changed Apple Podcasts categories <https://podnews.net/article/apple-changed-podcast-categories-2019>`_
          List of changes between the old and the new categories.
    """
    pass


class NotSupportedByItunesWarning(PodgenWarning):
    """
    Indicates that PodGen is used in a way that may not be compatible with Apple
    Podcasts (previously known as iTunes).

    In some cases, this may be because PodGen has not been kept up-to-date with
    new features which Apple Podcasts has added support for. Please add an issue
    if that is the case!
    """
    pass

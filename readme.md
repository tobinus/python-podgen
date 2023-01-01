PodGen (forked from python-feedgen)
===================================

[![Build Status](https://github.com/tobinus/python-podgen/actions/workflows/run-tests.yaml/badge.svg)](https://github.com/tobinus/python-podgen/actions/workflows/run-tests.yaml)
[![Documentation Status](https://readthedocs.org/projects/podgen/badge/?version=latest)](http://podgen.readthedocs.io/en/latest/?badge=latest)


This module can be used to generate podcast feeds in RSS format, and is
compatible with Python 3.7+.

It is licensed under the terms of both, the FreeBSD license and the LGPLv3+.
Choose the one which is more convenient for you. For more details have a look
at license.bsd and license.lgpl.

More details about the project:

- Repository:            https://github.com/tobinus/python-podgen
- Documentation:         https://podgen.readthedocs.io/
- Python Package Index:  https://pypi.python.org/pypi/podgen/


See the documentation link above for installation instructions and
guides on how to use this module.

Known bugs and limitations
--------------------------

* The updates to Apple's podcasting guidelines since 2016 have not been
  implemented. This includes the ability to mark episodes
  with episode and season number, and the ability to mark the podcast as
  "serial". It is a goal to implement those changes in a future release.
* We do not follow the RSS recommendation to encode &amp;, &lt; and &gt; using
  hexadecimal character reference (eg. `&#x3C;`), simply because lxml provides
  no documentation on how to do that when using the text property.

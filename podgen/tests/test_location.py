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

import unittest
import warnings
from podgen import Location

class TestTranscript(unittest.TestCase):
    def setUp(self):
        self.text = "My location"
        self.osm = "W5013364"
        self.geo = "geo:37.786971,-122.399677,300;crs=wgs84;u=100"
        self.latitude = 37.786971
        self.longitude = -122.399677
        self.altitude = 300
        self.crs = "wgs84"
        self.uncertainty = 100

    def _location(self):
        return Location(self.text, osm=self.osm, geo=self.geo)

    def test_missingText(self):
        self.assertRaises(TypeError, Location)
        self.assertRaises(ValueError, Location, None, osm=self.osm, geo=self.geo)
        self.assertRaises(ValueError, Location, "", osm=self.osm, geo=self.geo)

    def test_onlyText(self):
        location = Location(self.text)
        assert location
        assert location.text == self.text
        assert location.osm is None
        assert location.geo is None

    def test_osmConstructor(self):
        location = Location(self.text, osm=self.osm)
        assert location
        assert location.text == self.text
        assert location.osm == self.osm
        assert location.geo is None

    def test_textTooLong(self):
        self.assertRaises(ValueError, Location, "A" * 200)
        location = self._location()
        self.assertRaises(ValueError, setattr, location, "text", "B" * 200)

    def test_setNewText(self):
        location = self._location()
        new_text = "New Text"
        location.text = new_text
        assert location.text == new_text

    def test_setWrongText(self):
        location = self._location()
        self.assertRaises(ValueError, setattr, location, "text", "")
        self.assertRaises(ValueError, setattr, location, "text", None)

    def set_setNewOsm(self):
        new_osm = "R113314"
        location = self._location()
        old_location_osm = location.osm
        location.osm = new_osm
        assert location.osm == new_osm
        assert location.osm != old_location_osm

        location.osm = ""
        assert location.osm is None

    def test_setWrongOsm(self):
        location = self._location()
        self.assertRaises(ValueError, setattr, location, "osm", "invalid_osm")

    def test_wrongRegexGeo(self):
        geos = [
            "37.786971,-122.399677,300;crs=wgs84;u=100",
            "geo37.786971,-122.399677,300;crs=wgs84;u=100",
            "geo:37.786971;-122.399677;300;crs=wgs84;u=100",
            "geo:37.786971,-122.399677,300;crs=wgs84;foo=100",
            "geo:37.786971,-122.399677,300,crs=wgs84,u=100",
            "geo:abc,-122.399677,300;crs=wgs84;u=100",
            "geo:37.786971,-abc,300;crs=wgs84;u=100",
            "geo:37.786971,-122.399677,300;crs=wgs84;u=abc",
        ]
        for geo in geos:
            self.assertRaises(ValueError, Location, "text", geo=geo)

    def test_geoConstructor(self):
        location = Location(self.text, geo=self.geo)
        assert location
        assert location.text == self.text
        assert location.geo == self.geo

    def test_settingGeoWithoutGeoParemeter(self):
        location = Location(
            self.text,
            latitude=self.latitude,
            longitude=self.longitude,
            altitude=self.altitude,
            crs=self.crs,
            uncertainty=self.uncertainty
        )

        assert location.latitude == self.latitude
        assert location.longitude == self.longitude
        assert location.altitude == self.altitude
        assert location.crs == self.crs
        assert location.uncertainty == self.uncertainty

        geo = "geo:%s,%s,%s;crs=%s;u=%s" % \
              (self.latitude, self.longitude, self.altitude, self.crs, self.uncertainty)
        assert location.geo == geo

    def test_missingLatitudeOrLongitude(self):
        self.assertRaises(ValueError, Location, self.text, latitude=self.latitude)
        self.assertRaises(ValueError, Location, self.text, longitude=self.longitude)

    def test_geoParametersIgnored(self):
        other_latitude = 50
        other_longitude = 60
        other_altitude = 70
        other_crs = "foo"
        other_uncertainty = 10

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            location = Location(
                self.text,
                geo=self.geo,
                latitude=other_latitude,
                longitude=other_longitude,
                altitude=other_altitude,
                crs=other_crs,
                uncertainty=other_uncertainty
            )
            assert len(w) == 1
            assert str(w[0].message) == location._redundant_parameter_warning

        assert location.latitude != other_latitude
        assert location.longitude != other_longitude
        assert location.altitude != other_altitude
        assert location.crs != other_crs
        assert location.uncertainty != other_uncertainty

        geo = "geo:%s,%s,%s;crs=%s;u=%s" % \
              (self.latitude, self.longitude, self.altitude, self.crs, self.uncertainty)
        assert location.geo == geo

    def test_generatingGeoLatitudeLongitude(self):
        location = Location(
            self.text,
            latitude=self.latitude,
            longitude=self.longitude,
        )

        assert location.latitude == self.latitude
        assert location.longitude == self.longitude
        assert location.altitude is None
        assert location.crs is None
        assert location.uncertainty is None

        geo = "geo:%s,%s" % (self.latitude, self.longitude)
        assert location.geo == geo

    def test_generatingGeoLatitudeLongitudeAltitude(self):
        location = Location(
            self.text,
            latitude=self.latitude,
            longitude=self.longitude,
            altitude=self.altitude
        )

        assert location.latitude == self.latitude
        assert location.longitude == self.longitude
        assert location.altitude == self.altitude
        assert location.crs is None
        assert location.uncertainty is None

        geo = "geo:%s,%s,%s" % (self.latitude, self.longitude, self.altitude)
        assert location.geo == geo

    def test_generatingGeoLatitudeLongitudeCrs(self):
        location = Location(
            self.text,
            latitude=self.latitude,
            longitude=self.longitude,
            crs=self.crs,
        )

        assert location.latitude == self.latitude
        assert location.longitude == self.longitude
        assert location.altitude is None
        assert location.crs == self.crs
        assert location.uncertainty is None

        geo = "geo:%s,%s;crs=%s" % (self.latitude, self.longitude, self.crs)
        assert location.geo == geo

    def test_generatingGeoLatitudeLongitudeUncertainty(self):
        location = Location(
            self.text,
            latitude=self.latitude,
            longitude=self.longitude,
            uncertainty=self.uncertainty,
        )

        assert location.latitude == self.latitude
        assert location.longitude == self.longitude
        assert location.altitude is None
        assert location.crs is None
        assert location.uncertainty == self.uncertainty

        geo = "geo:%s,%s;u=%s" % (self.latitude, self.longitude, self.uncertainty)
        assert location.geo == geo

    def test_generatingGeoWithoutAltitude(self):
        location = Location(
            self.text,
            latitude=self.latitude,
            longitude=self.longitude,
            crs=self.crs,
            uncertainty=self.uncertainty,
        )

        assert location.latitude == self.latitude
        assert location.longitude == self.longitude
        assert location.altitude is None
        assert location.crs == self.crs
        assert location.uncertainty == self.uncertainty

        geo = "geo:%s,%s;crs=%s;u=%s" \
              % (self.latitude, self.longitude, self.crs, self.uncertainty)
        assert location.geo == geo

    def test_generatingGeoWithoutUncertainty(self):
        location = Location(
            self.text,
            latitude=self.latitude,
            longitude=self.longitude,
            altitude=self.altitude,
            crs=self.crs
        )

        assert location.latitude == self.latitude
        assert location.longitude == self.longitude
        assert location.altitude == self.altitude
        assert location.crs == self.crs
        assert location.uncertainty is None

        geo = "geo:%s,%s,%s;crs=%s" \
              % (self.latitude, self.longitude, self.altitude, self.crs)
        assert location.geo == geo

    def test_generatingGeoWithoutCrs(self):
        location = Location(
            self.text,
            latitude=self.latitude,
            longitude=self.longitude,
            altitude=self.altitude,
            uncertainty=self.uncertainty
        )

        assert location.latitude == self.latitude
        assert location.longitude == self.longitude
        assert location.altitude == self.altitude
        assert location.crs is None
        assert location.uncertainty == self.uncertainty

        geo = "geo:%s,%s,%s;u=%s" \
              % (self.latitude, self.longitude, self.altitude, self.uncertainty)
        assert location.geo == geo

    def test_settingLatitude(self):
        new_latitude = 45
        location = self._location()
        location.latitude = new_latitude

        new_geo = "geo:%s,%s,%s;crs=%s;u=%s" \
              % (new_latitude, self.longitude, self.altitude, self.crs, self.uncertainty)

        assert location.latitude == new_latitude
        assert location.geo == new_geo

    def test_settingLongitude(self):
        new_longitude = 55
        location = self._location()
        location.longitude = new_longitude

        new_geo = "geo:%s,%s,%s;crs=%s;u=%s" \
              % (self.latitude, new_longitude, self.altitude, self.crs, self.uncertainty)

        assert location.longitude == new_longitude
        assert location.geo == new_geo

    def test_settingAltitude(self):
        new_altitude = 23
        location = self._location()
        location.altitude = new_altitude

        new_geo = "geo:%s,%s,%s;crs=%s;u=%s" \
              % (self.latitude, self.longitude, new_altitude, self.crs, self.uncertainty)

        assert location.altitude == new_altitude
        assert location.geo == new_geo

    def test_settingCrs(self):
        new_crs = "tesla"
        location = self._location()
        location.crs = new_crs

        new_geo = "geo:%s,%s,%s;crs=%s;u=%s" \
                  % (self.latitude, self.longitude, self.altitude, new_crs, self.uncertainty)

        assert location.crs == new_crs
        assert location.geo == new_geo

    def test_settingUncertainty(self):
        new_uncertainty = 13
        location = self._location()
        location.uncertainty = new_uncertainty

        new_geo = "geo:%s,%s,%s;crs=%s;u=%s" \
                  % (self.latitude, self.longitude, self.altitude, self.crs, new_uncertainty)

        assert location.uncertainty == new_uncertainty
        assert location.geo == new_geo

    def test_setWrongLatitude(self):
        location = self._location()

        with self.assertRaises(ValueError):
            location.latitude = "text_not_float"

        with self.assertRaises(ValueError):
            location.latitude = "53.5eight"

    def test_setWrongLongitude(self):
        location = self._location()

        with self.assertRaises(ValueError):
            location.longitude = "text_not_float"

        with self.assertRaises(ValueError):
            location.longitude = "53.5eight"

    def test_setWrongAltitude(self):
        location = self._location()

        with self.assertRaises(ValueError):
            location.altitude = "text_not_float"

        with self.assertRaises(ValueError):
            location.altitude = "53.5eight"

    def test_setWrongUncertainty(self):
        location = self._location()

        with self.assertRaises(ValueError):
            location.uncertainty = "text_not_float"

        with self.assertRaises(ValueError):
            location.uncertainty = "53.5eight"

        with self.assertRaises(ValueError):
            location.uncertainty = -80

    def test_unknowCrs(self):
        location = self._location()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            location.crs = "unknow_system"
            assert len(w) == 1

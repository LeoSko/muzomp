# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from .models import Audio


class AudioTests(TestCase):
    def test_125_bpm_if_fast(self):
        a = Audio(bpm=125)
        self.assertIs(a.is_fast(), True)

    def test_110_bpm_not_fast(self):
        a = Audio(bpm=110)
        self.assertIs(a.is_fast(), False)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from os import path

import librosa
import numpy as np
from django.db import models
from django.utils import timezone


class Audio(models.Model):
    id = models.AutoField(primary_key=True, default=0)
    file = models.FileField(upload_to='storage/')
    artist = models.CharField(max_length=200, default='Unknown')
    title = models.CharField(max_length=200, default='Unknown')
    date_uploaded = models.DateTimeField('Date uploaded', default=timezone.now)


class BPM(models.Model):
    id = models.AutoField(primary_key=True, default=0)
    value = models.IntegerField()
    audio = models.OneToOneField(Audio, on_delete=models.CASCADE)
    start_time = models.TimeField()
    duration = models.DurationField()


class Query(models.Model):
    id = models.AutoField(primary_key=True, default=0)
    date_queued = models.DateTimeField('Date queued', default=timezone.now)
    priority = models.IntegerField()
    query = models.CharField(max_length=4000, default='N/A')


class Parameter(models.Model):
    id = models.AutoField(primary_key=True, default=0)
    name = models.CharField(max_length=200, default='Unknown')
    description = models.CharField(max_length=4000, default='Please, fill in description field')


class PreLoadedAudio(models.Model):
    id = models.AutoField(primary_key=True)
    file = models.FileField(upload_to='not_processed/')
    priority = models.IntegerField(default=0)
    date_uploaded = models.DateTimeField('Date uploaded', default=timezone.now)
    status = models.CharField(max_length=200, default='Ready to process')

    def get_filename(self):
        return path.basename(self.file.url)

    def get_bpm(self):
        # FIXME
        path_file = '/opt/muzompmuzomp' + self.file.url
        tmp = open(path_file, "rb").read()
        y, sr = librosa.load(path_file, offset=6, duration=11)
        onset_env = librosa.onset.onset_strength(y, sr=sr)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
        return np.round(tempo, 1)

    def get_duration(self):
        return librosa.get_duration(filename=self.file.url)


class ProcessQuery(models.Model):
    id = models.AutoField(primary_key=True, default=0)
    pla = models.OneToOneField(PreLoadedAudio, on_delete=models.CASCADE)
    priority = models.IntegerField()
    start_time = models.TimeField()
    duration = models.DurationField()
    parameter = models.OneToOneField(Parameter, on_delete=models.CASCADE)
    date_queued = models.DateTimeField('Date queued', default=timezone.now)
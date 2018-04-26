# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
from os import path
from urllib import parse

import librosa
from django.db import models
from django.utils import timezone


class Audio(models.Model):
    IN_QUEUE = 0
    PROCESSING = 1
    PROCESSED = 2
    STATUS_CHOICES = (
        (IN_QUEUE, 'In queue'),
        (PROCESSING, 'Processing'),
        (PROCESSED, 'Processed'),
    )

    id = models.AutoField(primary_key=True)
    file = models.FileField(upload_to='storage/')
    artist = models.CharField(max_length=200, default='Unknown')
    title = models.CharField(max_length=200, default='Unknown')
    date_uploaded = models.DateTimeField('Date uploaded', default=timezone.now)
    status = models.IntegerField(default=IN_QUEUE)
    tasks_scheduled = models.IntegerField(default=-1)
    tasks_processed = models.IntegerField(default=0)

    def get_duration(self):
        return datetime.timedelta(seconds=librosa.get_duration(filename=parse.unquote(self.file.url)))

    def get_filename(self):
        return path.basename(self.file.url)

    def update_status(self):
        if self.tasks_scheduled == self.tasks_processed:
            self.status = Audio.PROCESSED
        elif self.tasks_processed > 0:
            self.status = Audio.PROCESSING

    def increase_processed_tasks(self):
        self.tasks_processed = self.tasks_processed + 1
        self.update_status()


class BPM(models.Model):
    """
    BPM (beats per minute)

    Parameters
    -------------
    id : django.models.AutoField
        Auto-incremented id

    value : int > 0
        Actual value of object
    """
    IN_QUEUE = 0
    PROCESSING = 1
    PROCESSED = 2
    STATUS_CHOICES = (
        (IN_QUEUE, 'In queue'),
        (PROCESSING, 'Processing'),
        (PROCESSED, 'Processed'),
    )

    id = models.AutoField(primary_key=True)
    value = models.IntegerField(default=-1)
    audio = models.ForeignKey(Audio, on_delete=models.DO_NOTHING)
    start_time = models.FloatField()
    duration = models.DurationField()
    status = models.IntegerField(default=IN_QUEUE)

    def start(self):
        return datetime.timedelta(seconds=self.start_time)

    def end(self):
        return datetime.timedelta(seconds=self.start_time + self.duration.total_seconds())

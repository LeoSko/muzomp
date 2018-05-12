# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
from os import path

from django.db import models
from django.utils import timezone


class Audio(models.Model):
    IN_QUEUE = 0
    PROCESSING = 1
    PROCESSED = 2
    SCHEDULED = 3
    STATUS_CHOICES = (
        (SCHEDULED, 'Scheduled'),
        (IN_QUEUE, 'In queue'),
        (PROCESSING, 'Processing'),
        (PROCESSED, 'Processed'),
    )
    DEFAULT_ARTIST = 'Unknown'
    DEFAULT_TITLE = 'Unknown'
    DEFAULT_HASH = 'N/A'

    id = models.AutoField(primary_key=True)
    file = models.FileField(upload_to='storage/')
    file_hash = models.CharField(max_length=32, default=DEFAULT_HASH)
    artist = models.CharField(max_length=200, default=DEFAULT_ARTIST)
    title = models.CharField(max_length=200, default=DEFAULT_TITLE)
    duration = models.FloatField(null=True)
    filename = models.CharField(max_length=255, default='')
    date_uploaded = models.DateTimeField('Date uploaded', default=timezone.now)
    status = models.IntegerField(default=SCHEDULED)
    tasks_processed = models.IntegerField(default=0)
    tasks_scheduled = models.IntegerField(default=-1)
    avg_bpm = models.IntegerField(default=-1)

    def get_filename(self):
        return path.basename(self.file.url)

    def __str__(self):
        return "Audio(id={0}, file={1}, artist={2}, title={3}, date_uploaded={4}, status={5}, tasks={6}/{7})" \
            .format(self.id, self.file, self.artist, self.title, self.date_uploaded, Audio.STATUS_CHOICES[self.status],
                    self.tasks_processed, self.tasks_scheduled)

    def is_fast(self):
        return self.avg_bpm > 120


class BPM(models.Model):
    """
    BPM (beats per minute)

    Parameters
    -------------
    BPM.id : django.models.AutoField
        Auto-incremented id

    BPM.value : int > 0
        Actual calculated BPM value
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
    duration = models.FloatField()
    status = models.IntegerField(default=IN_QUEUE)
    processing_start = models.DateTimeField(null=True)
    processing_end = models.DateTimeField(null=True)
    task_id = models.IntegerField(default=0)

    def start(self):
        return datetime.timedelta(seconds=self.start_time)

    def end(self):
        return datetime.timedelta(seconds=self.start_time + self.duration)

    def __str__(self):
        return "BPM(id={0}, value={1}, audio={2}, start_time={3}, duration={4}, status={5})" \
            .format(self.id, self.value, self.audio, self.start_time, self.duration, BPM.STATUS_CHOICES[self.status])

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
from os import path

from django.db import models
from django.utils import timezone

DEFAULT_ARTIST = 'Unknown'
DEFAULT_TITLE = 'Unknown'
DEFAULT_HASH = 'N/A'


class State(models.Model):
    """
    State (snapshot of statically calculated params for system)

    Parameters
    -------------
    hash_id : django.models.CharField
        Hashed id out of Audio.id set into md5

    pc : django.models.CharField
        Json-encoded matrix of principal components for this set of audio ids

    calculated_date : django.models.DateTimeField
        Date of calculated global principal components matrix

    means : django.models.CharField
        Json-encoded array of means of audio ids

    stds : django.models.CharField
        Json-encoded array of stds of audio ids
    """
    hash_id = models.CharField(max_length=32, default=DEFAULT_HASH, primary_key=True)
    calculated_date = models.DateTimeField(default=timezone.now)
    pc = models.CharField(max_length=100000)
    means = models.CharField(max_length=1000)
    stds = models.CharField(max_length=1000)


class Audio(models.Model):
    """
    Audio

    Parameters
    -------------
    id : django.models.AutoField
        Primary key, announcemented by Django

    file : django.models.FileField
        File of audio in filesystem, usually it is *.mp3 file

    file_hash : django.models.CharField
        Hash of file, used to reject same files on upload

    artist : django.models.CharField
        Artist of audio, taken using ID tags

    title : django.models.CharField
        Title of audio, taken using ID tags

    duration : django.models.FloatField
        Duration of audio, taken using librosa method get_duration

    filename : django.models.CharField
        Filename of audio on filesystem

    date_uploaded : django.models.DateTimeField
        Date and time of file upload

    status : core.models.Audio.STATUS_CHOICES
        Status of this audio processing

    tasks_processed : django.models.IntegerField
        Approximate count of tasks that is for sure already processed for this audio

    tasks_scheduled : django.models.IntegerField
        Count of tasks that will be processed overall for this audio

    avg_bpm : django.models.IntegerField
        Average BPM for this track

    principal_component : django.models.CharField
        Principal components of this Audio.
        Used to calculate distance between tracks in term of their spectral representation

    closest_list : django.models.CharField
        Cached list of closest audio to this particular audio
    """
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

    id = models.AutoField(primary_key=True)
    file = models.FileField(upload_to='storage/')
    file_hash = models.CharField(max_length=32, default=DEFAULT_HASH)
    artist = models.CharField(max_length=200, default=DEFAULT_ARTIST)
    title = models.CharField(max_length=200, default=DEFAULT_TITLE)
    duration = models.FloatField(null=True)
    filename = models.CharField(max_length=255, default='')
    file_url = models.CharField(max_length=255, default='')
    date_uploaded = models.DateTimeField('Date uploaded', default=timezone.now)
    status = models.IntegerField(default=SCHEDULED)
    tasks_processed = models.IntegerField(default=0)
    tasks_scheduled = models.IntegerField(default=-1)
    avg_bpm = models.IntegerField(default=-1)
    principal_components = models.CharField(max_length=2000, null=True)
    closest_list = models.CharField(max_length=2000, null=True)

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
    id : django.models.AutoField
        Auto-incremented id

    audio : django.models.ForeignKey
        Audio that is connected to this BPM task

    value : django.models.IntegerField
        Actual calculated BPM value

    start_time : django.models.FloatField
        The beginning of this BPM part of Audio, in seconds

    duration : django.models.FloatField
        The duration of this BPM part of Audio, in seconds

    status : core.models.BPM.STATUS_CHOICES
        Status of processing this BPM tasks

    processing_start : django.models.DateTimeField
        Start of this task processing, used to determine lost tasks

    processing_end : django.models.DateTimeField
        End of this task processing, used for statistics and optimisations
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
    audio = models.ForeignKey(Audio, on_delete=models.DO_NOTHING)
    value = models.IntegerField(default=-1)
    start_time = models.FloatField()
    duration = models.FloatField()
    status = models.IntegerField(default=IN_QUEUE)
    processing_start = models.DateTimeField(null=True)
    processing_end = models.DateTimeField(null=True)

    def start(self):
        return datetime.timedelta(seconds=self.start_time)

    def end(self):
        return datetime.timedelta(seconds=self.start_time + self.duration)

    def __str__(self):
        return "BPM(id={0}, value={1}, audio={2}, start_time={3}, duration={4}, status={5})" \
            .format(self.id, self.value, self.audio, self.start_time, self.duration, BPM.STATUS_CHOICES[self.status])

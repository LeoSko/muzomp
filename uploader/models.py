# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid
from os import path
from django.core.files.storage import FileSystemStorage
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from django.db import models
import librosa
import numpy as np

class PreLoadedAudio(models.Model):
	id = models.AutoField(primary_key=True)
	file = models.FileField(upload_to='not_processed/')
	priority = models.IntegerField(default=0)
	date_uploaded = models.DateTimeField('Date uploaded', default=timezone.now)
	status = models.CharField(max_length=200, default='Ready to process')

	def get_filename(self):
		return path.basename(self.file.url)

	def get_bpm(self):
		#FIXME
		path_file = '/opt/sms' + self.file.url
		tmp = open(path_file, "rb").read()
		y, sr = librosa.load(path_file,offset = 6, duration = 11)
		onset_env = librosa.onset.onset_strength(y, sr=sr)
		tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
		return np.round(tempo, 1)

	def get_duration(self):
		return librosa.get_duration(filename=self.file.url)

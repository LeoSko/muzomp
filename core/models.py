# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid
from django.core.files.storage import FileSystemStorage
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from django.db import models
from uploader.models import PreLoadedAudio

class Audio(models.Model):
	id = models.AutoField(primary_key=True, default=0)
	file = models.FileField(upload_to='storage/')
	artist = models.CharField(max_length=200, default='Unknown')
	title = models.CharField(max_length=200, default='Unknown')
	date_uploaded = models.DateTimeField('Date uploaded', default=timezone.now)
	

class BPM(models.Model):
	id = models.AutoField(primary_key=True, default=0)
	value = models.IntegerField()
	audio = models.OneToOneField(Audio)
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

	
class ProcessQuery(models.Model):
	id = models.AutoField(primary_key=True, default=0)
	pla = models.OneToOneField(PreLoadedAudio)
	priority = models.IntegerField()
	start_time = models.TimeField()
	duration = models.DurationField()
	parameter = models.OneToOneField(Parameter)
	date_queued = models.DateTimeField('Date queued', default=timezone.now)

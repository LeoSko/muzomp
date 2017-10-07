# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import psutil
from time import gmtime, strftime
import uuid
from django.core.files.storage import FileSystemStorage
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from django.db import models

class Stats(models.Model):
    @staticmethod
    def get_disk_usage(): 
        statvfs = os.statvfs('/')
        b_in_gb = 1024 ** 3
        full = statvfs.f_frsize * statvfs.f_blocks
        free = statvfs.f_frsize * statvfs.f_bfree
        disk_usage = "Disk usage: " + str(round((full-free)/b_in_gb,1))+" Gb / "+str(round(full/b_in_gb,1)) + " Gb " +"("+str(round((full - free)/full *100,2))+"%)"
        return disk_usage
    @staticmethod
    def get_cpu_usage(): 
        (load1, load5, load15) = os.getloadavg()
        cpu_usage = "CPU Usage: " + str(load1)+ "% in 1 min / "+ str(load5)+ "% in 5 min / "+str(load15)+ "% in 15 min"
        return cpu_usage
    @staticmethod
    def get_date_time(): 
        date_time = "Date and time of request: "+strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " GMT"
        return date_time

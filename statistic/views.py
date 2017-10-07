from django.http import HttpResponse
from time import gmtime, strftime
from django.shortcuts import render
import os
import psutil

from .models import Stats

def index(request):
    disk_usage = Stats.get_disk_usage()
    cpu_usage = Stats.get_cpu_usage()
    date_time = Stats.get_date_time()
    context = {'disk_usage': disk_usage,'cpu_usage': cpu_usage,'date_time': date_time}
    return render(request,'statistic/index.html',context)
 #   statvfs = os.statvfs('/')
  #  b_in_gb = 1073741824
   # full = statvfs.f_frsize * statvfs.f_blocks
   # free = statvfs.f_frsize * statvfs.f_bfree
   # disk_usage = "Disk usage: " + str(round((full-free)/b_in_gb,1))+" Gb / "+str(round(full/b_in_gb,1)) + " Gb " +"("+str(round((full - free)/full *100,2))+"%)"
   # (load1, load5, load15) = os.getloadavg()
   # cpu_usage = "CPU Usage: " + str(load1)+ "% in 1 min / "+ str(load5)+ "% in 5 min / "+str(load15)+ "% in 15 min"
   # date_time = "Date and time of request: "+strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " GMT"
   # response = disk_usage +"<br />"+ cpu_usage  +"<br />" + date_time
   

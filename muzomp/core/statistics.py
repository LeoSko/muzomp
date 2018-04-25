import psutil

from django.db import models


class Stats(models.Model):
    @staticmethod
    def sizeof_fmt(num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    @staticmethod
    def get_disk_usage():
        return psutil.disk_usage(".").percent

    @staticmethod
    def get_disk_free_space():
        return Stats.sizeof_fmt(psutil.disk_usage(".").free)

    @staticmethod
    def get_disk_full_space():
        return Stats.sizeof_fmt(psutil.disk_usage(".").total)

    @staticmethod
    def get_cpu_usage():
        return psutil.cpu_percent(0, True)


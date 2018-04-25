import rabbitpy as rabbitpy
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from datetime import timedelta

from core import tasks
from core.statistics import Stats
from .models import Audio, BPM


class IndexView(generic.TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['queue'] = Audio.objects.filter(status=Audio.IN_QUEUE).order_by('date_uploaded')[:10]
        context['processing'] = Audio.objects.filter(status=Audio.PROCESSING).order_by('date_uploaded')[:10]
        context['audio'] = Audio.objects.filter(status=Audio.PROCESSED).order_by('date_uploaded')[:10]
        context['bpm'] = BPM.objects.filter(status=BPM.PROCESSED).order_by('id').reverse()[:10]
        return context


class AudioView(generic.DetailView):
    template_name = 'core/audio.html'
    context_object_name = 'audio'


class QueueView(generic.TemplateView):
    template_name = 'core/queue.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks_info'] = ''
        with rabbitpy.Connection('amqp://muzomp:muzomp@localhost:5672') as conn:
            with conn.channel() as channel:
                for message in rabbitpy.Queue(channel, 'celery '):
                    context['tasks_info'] += str(message)
        return context


class QueryView(generic.TemplateView):
    template_name = 'core/query.html'


class UploaderView(generic.TemplateView):
    template_name = 'core/upload.html'

    def post(self, request, *args, **kwargs):
        if request.FILES:
            a = Audio.objects.create(file=request.FILES['audio'])
            a.save()
            duration = a.get_duration().seconds
            subtime = 15
            start_time = 0
            a.tasks_scheduled = duration // subtime
            a.save()
            while start_time < duration - subtime * 2:
                bpm = BPM.objects.create(audio=a, start_time=start_time, duration=timedelta(subtime), value=-1)
                bpm.save()
                tasks.process_bpm.delay(bpm.id)
                start_time = start_time + subtime
            bpm = BPM.objects.create(audio=a, start_time=start_time,
                                     duration=timedelta(duration - (subtime * (a.tasks_scheduled - 1))), value=-1)
            bpm.save()
            tasks.process_bpm.delay(bpm.id)
            return HttpResponseRedirect(reverse('core:index'))
        else:
            return HttpResponseRedirect(reverse('core:upload'))


class StatisticView(generic.TemplateView):
    template_name = 'core/statistic.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disk_usage'] = Stats.get_disk_usage()
        context['disk_free_space'] = Stats.get_disk_free_space()
        context['disk_total_space'] = Stats.get_disk_full_space()
        context['cpu_usage'] = Stats.get_cpu_usage()
        context['tracks_count'] = Audio.objects.count()
        context['processing'] = Audio.objects.filter(status=Audio.PROCESSING).order_by('date_uploaded')[:10]
        return context

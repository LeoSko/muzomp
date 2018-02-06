from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from core import tasks
from .models import Audio, BPM
from celery import app


class IndexView(generic.TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['queue'] = Audio.objects.filter(status=Audio.IN_QUEUE).order_by('date_uploaded')[:10]
        context['processing'] = Audio.objects.filter(status=Audio.PROCESSING).order_by('date_uploaded')[:10]
        context['audio'] = Audio.objects.filter(status=Audio.PROCESSED).order_by('date_uploaded')[:10]
        context['bpm'] = BPM.objects.order_by('id').reverse()[:10]
        return context


class AudioView(generic.DetailView):
    template_name = 'core/audio.html'
    context_object_name = 'audio'


class QueueView(generic.TemplateView):
    template_name = 'core/queue.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks_info'] = app.tasks
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
                tasks.process.delay(a.id, start_time, subtime, 'BPM')
                start_time = start_time + subtime
            tasks.process.delay(a.id, start_time, duration - (subtime * (a.tasks_scheduled - 1)), 'BPM')
            return HttpResponseRedirect(reverse('core:index'))
        else:
            return HttpResponseRedirect(reverse('core:upload'))


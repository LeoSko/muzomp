import hashlib
import json
from os import path
from urllib import parse
from urllib.parse import unquote

import librosa
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views import generic
from eyed3 import id3

from core import tasks
from core.statistics import Stats
from .models import Audio, BPM, DEFAULT_ARTIST, DEFAULT_TITLE


class IndexView(generic.TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class IndexQueueView(generic.TemplateView):
    template_name = 'index/queue.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        statuses = [Audio.IN_QUEUE, Audio.SCHEDULED]
        context['queue'] = Audio.objects.filter(status__in=statuses).order_by('date_uploaded')[:10]
        return context


class IndexAudioView(generic.TemplateView):
    template_name = 'index/audio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['audio'] = Audio.objects.filter(status=Audio.PROCESSED).order_by('date_uploaded')[:10]
        return context


class IndexProcessingView(generic.TemplateView):
    template_name = 'index/processing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['processing'] = Audio.objects.filter(status=Audio.PROCESSING).order_by('date_uploaded')[:10]
        return context


class AudioView(generic.TemplateView):
    template_name = 'core/audio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['a'] = Audio.objects.get(id=kwargs['audio_id'])
        context['bpms'] = BPM.objects.filter(audio=context['a'])
        return context


class AudioDataView(generic.View):
    @staticmethod
    def get(request, audio_id):
        a = Audio.objects.get(id=audio_id)
        response_data = {'artist': a.artist, 'title': a.title, 'duration': a.duration,
                         'finished': (a.status == Audio.PROCESSED), 'avg_bpm': a.avg_bpm}
        return HttpResponse(json.dumps(response_data), content_type="application/json")


class AudioBPMView(generic.TemplateView):
    template_name = 'audio/bpm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bpms'] = BPM.objects.filter(audio__id=kwargs['audio_id'])
        return context


class AudioBPMDataView(generic.View):
    @staticmethod
    def get(request, audio_id):
        response_data = {}
        bpms = BPM.objects.filter(audio__id=audio_id).order_by('start_time')
        if bpms.count() > 0:
            response_data['bpm_values'] = list(bpms.values_list('value', flat=True))
            response_data['bpm_values'].append(bpms.last().value)
            response_data['time_values'] = list(bpms.values_list('start_time', flat=True))
            response_data['time_values'].append(bpms.last().start_time + bpms.last().duration)
            response_data['time_labels'] = response_data['time_values']
            response_data['finished'] = len(bpms.exclude(status=BPM.PROCESSED)) == 0
        return HttpResponse(json.dumps(response_data), content_type="application/json")


class QueueView(generic.TemplateView):
    template_name = 'core/queue.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bpm'] = BPM.objects.filter(status=BPM.IN_QUEUE).order_by('id').reverse()[:50]
        context['audio'] = Audio.objects.filter(status=Audio.IN_QUEUE).order_by('id').reverse()[:50]
        return context


class QueryView(generic.TemplateView):
    template_name = 'core/query.html'


class UploadView(generic.View):
    @staticmethod
    def get_file_obj(file):
        if isinstance(file, InMemoryUploadedFile):
            return file
        elif isinstance(file, TemporaryUploadedFile):
            return file.file.file
        else:
            raise FileNotFoundError("Unknown type of file for hash calculation")

    @staticmethod
    def hash_file(file, algorithm='md5', buffer_size=8192):
        h = hashlib.new(algorithm)
        block = file.read(buffer_size)
        if not block:
            return h.digest()
        h.update(block)
        return h.hexdigest()

    @staticmethod
    def post(request):
        response_data = {}
        if request.FILES:
            response_data['link'] = []
            for file in request.FILES.getlist('audio'):
                file_hash = UploadView.hash_file(UploadView.get_file_obj(file))
                check = Audio.objects.filter(file_hash=file_hash)
                if check.count() > 0:
                    response_data['link'].append(reverse('core:audio', kwargs={'audio_id': check[0].id}))
                    continue
                tag = id3.Tag()
                tag.parse(file)
                if tag.artist is None:
                    tag.artist = DEFAULT_ARTIST
                else:
                    tag.artist = str(tag.artist).encode('cp1252').decode('cp1251')
                if tag.title is None:
                    tag.title = DEFAULT_TITLE
                else:
                    tag.title = str(tag.title).encode('cp1252').decode('cp1251')
                a = Audio.objects.create(file=file, artist=tag.artist, title=tag.title, file_hash=file_hash)
                a.save()
                a.duration = librosa.get_duration(filename=parse.unquote(a.file.url))
                a.filename = unquote(path.basename(a.file.url))
                a.save()
                tasks.schedule_audio_tasks.delay(a.id)
                response_data['link'].append(reverse('core:audio', kwargs={'audio_id': a.id}))
        else:
            response_data['error'] = 'No files found in request'
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    @staticmethod
    def get(request):
        return HttpResponseRedirect(reverse('core:upload_form'))


class UploaderFormView(generic.TemplateView):
    template_name = 'core/upload.html'


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

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from .models import Audio, PreLoadedAudio, BPM


class IndexView(generic.TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['last_pla'] = PreLoadedAudio.objects.order_by('date_uploaded').reverse()[:10]
        context['last_audio'] = Audio.objects.order_by('date_uploaded').reverse()[:10]
        context['last_bpm'] = BPM.objects.order_by('id').reverse()[:10]
        return context


class AudioView(generic.DetailView):
    template_name = 'core/audio.html'
    context_object_name = 'audio'


class ProcessQueryView(generic.ListView):
    template_name = 'core/processquerylist.html'
    context_object_name = 'queries'


class QueryView(generic.ListView):
    template_name = 'core/query.html'
    context_object_name = 'query'


class QueueView(generic.ListView):
    template_name = 'core/queue.html'
    context_object_name = 'queue'


class UploaderView(generic.TemplateView):
    template_name = 'core/upload.html'

    def post(self, request, *args, **kwargs):
        if request.FILES:
            pla = PreLoadedAudio.objects.create(file=request.FILES['audio'])
            pla.save()
            a = Audio.objects.create(file=pla.file)
            a.save()
            bpm = BPM.objects.create(audio=a, start_time=0, duration=pla.get_duration(), value=pla.get_bpm())
            bpm.save()
            pla.delete()
            return HttpResponseRedirect(reverse('core:index'))
        else:
            return HttpResponseRedirect(reverse('core:upload'))


class PreLoadedAudioView(generic.DetailView):
    template_name = 'pla.html'
    context_object_name = 'pla'

# TODO look for file in DB

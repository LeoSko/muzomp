from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from .models import Audio, PreLoadedAudio, BPM


class IndexView(generic.TemplateView):
    template_name = 'core/index.html'
    context_object_name = 'context'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['last_pla'] = PreLoadedAudio.objects.order_by('date_uploaded').reverse()[:10]
        context['last_audio'] = Audio.objects.order_by('date_uploaded').reverse()[:10]
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


class UploaderView(generic.TemplateView):
    template_name = 'core/upload.html'

    def post(self, request, *args, **kwargs):
        if request.FILES:
            pla = PreLoadedAudio.objects.create(file=request.FILES['audio'])
            pla.save()
            a = Audio.objects.create(file=pla.file)
            bpm = BPM.objects.create(audio=a, start_time=0, duration=pla.get_duration(), value=pla.get_bpm())
            a.save()
            bpm.save()
            pla.delete()
            return HttpResponseRedirect(reverse('core:index'))
        else:
            return HttpResponseRedirect(reverse('uploader:index'))


class PreLoadedAudioView(generic.DetailView):
    template_name = 'pla.html'
    context_object_name = 'pla'

# TODO look for file in DB

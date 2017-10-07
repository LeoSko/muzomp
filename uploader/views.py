from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.utils  import timezone

from .models import PreLoadedAudio
from core.models import Audio, BPM

class UploaderView(generic.TemplateView):
	template_name = 'uploader/index.html'

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

	#TODO look for file in DB

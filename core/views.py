from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.utils  import timezone

from .models import Audio
from uploader.models import PreLoadedAudio

class IndexView(generic.TemplateView):
	template_name = 'core/index.html'
	context_object_name = 'context'

	def get_context_data(self, **kwargs):
		context = super(IndexView, self).get_context_data(**kwargs)
		context['last_pla'] = PreLoadedAudio.objects.order_by('date_uploaded')[:10].reverse()
		context['last_audio'] = Audio.objects.order_by('date_uploaded')[:10].reverse()
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

# Create your tasks here
from __future__ import absolute_import, unicode_literals

from datetime import timedelta

import librosa
import numpy as np
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

from core.models import Audio, BPM
from django.db import transaction


@shared_task(name='core.tasks.process')
def process(pla_id, start_time, duration, parameter):
    try:
        a = Audio.objects.get(id=pla_id)
    except ObjectDoesNotExist:
        return 1
    if parameter == 'BPM':
        y, sr = librosa.load(a.file.url)
        onset_env = librosa.onset.onset_strength(y, sr=sr)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
        val = np.round(tempo, 1)

        bpm = BPM.objects.create(audio=a, start_time=start_time, duration=timedelta(seconds=duration), value=val)
        bpm.save()
        with transaction.atomic():
            a.increase_processed_tasks()
            a.save()

    return 0

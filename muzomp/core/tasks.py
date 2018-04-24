# Create your tasks here
from __future__ import absolute_import, unicode_literals

from datetime import timedelta
from urllib.parse import unquote

import librosa
import numpy as np
from celery.decorators import task
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .models import Audio, BPM

SUCCESS_CODE = 0
OBJECT_DOES_NOT_EXIST_ERROR_CODE = -9
UNKNOWN_PARAMETER_ERROR_CODE = -1
WRONG_ARRAY_LENGTH = -2


@task(name='core.tasks.process')
def process(audio_id, start_time, duration, parameter):
    try:
        a = Audio.objects.get(id=audio_id)
    except ObjectDoesNotExist:
        return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    if parameter == 'BPM':
        y, sr = librosa.load(unquote(a.file.url))
        onset_env = librosa.onset.onset_strength(y, sr=sr)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
        val = np.round(tempo, 1)

        bpm = BPM.objects.create(audio=a, start_time=start_time, duration=timedelta(seconds=duration), value=val)
        bpm.save()
        with transaction.atomic():
            a.refresh_from_db()
            a.increase_processed_tasks()
            a.save()
            if a.status == Audio.PROCESSED:
                merge.delay(audio_id, parameter)
        return SUCCESS_CODE

    return UNKNOWN_PARAMETER_ERROR_CODE


@task(name='core.tasks.merge')
def merge(audio_id, parameter):
    try:
        a = Audio.objects.get(id=audio_id)
    except ObjectDoesNotExist:
        return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    if parameter == 'BPM':
        bpms = BPM.objects.filter(audio=a).order_by('start_time')
        if bpms.count() < 2:
            return WRONG_ARRAY_LENGTH
        new_bpms = [bpms[0]]
        for old_bpm in bpms:
            if old_bpm.value == new_bpms[-1].value:
                new_bpms[-1].duration += old_bpm.duration
            else:
                new_bpms.append(old_bpm)
            old_bpm.delete()
        for new_bpm in new_bpms:
            new_bpm.save()
        return SUCCESS_CODE
    return UNKNOWN_PARAMETER_ERROR_CODE

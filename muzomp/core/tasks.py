# Create your tasks here
from __future__ import absolute_import, unicode_literals

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


@task(name='core.tasks.process_bpm')
def process_bpm(task_id):
    bpm = BPM.objects.get(id=task_id)
    if bpm.status == BPM.PROCESSED:
        return SUCCESS_CODE
    bpm.status = BPM.PROCESSING
    bpm.save()
    y, sr = librosa.load(unquote(bpm.a.file.url), offset=bpm.start_time)
    onset_env = librosa.onset.onset_strength(y, sr=sr)
    tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
    bpm.value = np.round(tempo, 1)
    bpm.a.increase_processed_tasks()
    bpm.status = BPM.PROCESSED
    bpm.save()

    if bpm.a.status == Audio.PROCESSED:
        merge.delay(bpm.a.audio_id, 'BPM')
    return SUCCESS_CODE


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

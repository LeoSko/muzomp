# Create your tasks here
from __future__ import absolute_import, unicode_literals

import datetime
from urllib.parse import unquote

import librosa
import numpy as np
from celery.task import task
from django.core.exceptions import ObjectDoesNotExist
from django.db import OperationalError

from .models import Audio, BPM

SUCCESS_CODE = 0
OBJECT_DOES_NOT_EXIST_ERROR_CODE = -9
UNKNOWN_PARAMETER_ERROR_CODE = -1
WRONG_ARRAY_LENGTH = -2
UNKNOWN_ERROR = -3


@task(name='core.tasks.process_bpm', autoretry_for=(OperationalError,))
def process_bpm(task_id):
    try:
        bpm = BPM.objects.get(id=task_id)
    except ObjectDoesNotExist:
        return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    if bpm.status == BPM.PROCESSED:
        return SUCCESS_CODE
    bpm.status = BPM.PROCESSING
    bpm.save()
    y, sr = librosa.load(unquote(bpm.audio.file.url), offset=bpm.start_time, duration=bpm.duration.total_seconds())
    onset_env = librosa.onset.onset_strength(y, sr=sr)
    tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
    bpm.value = np.round(tempo, 1)
    bpm.status = BPM.PROCESSED
    bpm.save()
    bpm.audio.increase_processed_tasks()
    bpm.audio.save()

    if Audio.objects.get(id=bpm.audio.id).status == Audio.PROCESSED:
        merge.delay(bpm.audio.id, 'BPM')
    return SUCCESS_CODE


@task(name='core.tasks.merge', autoretry_for=(OperationalError,))
def merge(audio_id, parameter):
    try:
        a = Audio.objects.get(id=audio_id)
    except ObjectDoesNotExist:
        return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    if parameter == 'BPM':
        bpms = BPM.objects.filter(audio=a).order_by('start_time')
        if bpms.count() < 2:
            return WRONG_ARRAY_LENGTH
        t_bpm = bpms[0]
        res_bpm = []
        for i in range(1, len(bpms)):
            old_bpm = bpms[i]
            if old_bpm.value == t_bpm.value:
                t_bpm.duration += old_bpm.duration
            else:
                res_bpm.append(t_bpm)
                t_bpm = old_bpm
        res_bpm.append(t_bpm)
        bpms.delete()
        BPM.objects.bulk_create(res_bpm)
        return SUCCESS_CODE
    return UNKNOWN_PARAMETER_ERROR_CODE


@task(name='core.tasks.count_avg_bpm')
def count_avg_bpm(audio_id):
    try:
        a = Audio.objects.get(id=audio_id)
    except ObjectDoesNotExist:
        return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    values = BPM.objects.filter(audio=a).order_by('start_time').values_list('value', flat=True)
    weights = list(map(datetime.timedelta.total_seconds, BPM.objects.filter(audio=a).order_by('start_time')
                       .values_list('duration', flat=True)))
    a.avg_bpm = sum(x * y for x, y in zip(weights, values)) / sum(weights)
    a.save()
    return SUCCESS_CODE

@task(name='core.tasks.get_principal_components')
def get_principal_components(files_list, varianceShare):
    A = np.zeros(shape=(13696, len(files_list)), dtype=float)
    nf = 0
    for file in files_list:
        y, sr = librosa.load('music1/' + file, offset=15, duration=10)
        D = librosa.stft(y, n_fft=2048)
        X = np.abs(D)
        i = 0
        j = 0
        k = 0
        while i < 1024:
            while j < 428:
                s = 0
                for ii in range(i, i + 7):
                    for jj in range(j, j + 3):
                        s += X[ii][jj]
                A[k][nf] = s / 32
                k = k + 1
                j = j + 4
            j = 0
            i = i + 8
        nf = nf + 1
    A.resize(8000, len(files_list))
    means = np.mean(A, 1)
    stds = np.std(A, 1)
    for i in range(len(means)):
        A[i, :] = A[i, :] - means[i]
        A[i, :] = A[i, :] / stds[i]
    R = np.cov(A)
    D, V = np.linalg.eigh(R)

    componentNumber = 0  # число главных компонент
    sumsum = 0
    for k in range(len(D)):
        sumsum = sumsum + D[8000 - 1 - k]
    semisum = 0
    for k in range(len(D)):
        semisum = semisum + D[8000 - 1 - k]
        if semisum / sumsum >= varianceShare:
            componentNumber = k + 1
            break
    principalVectors = np.zeros((8000, componentNumber))
    for k in range(componentNumber):
        principalVectors[:, k] = V[:, 8000 - 1 - k]
    PC = np.dot(A.T, principalVectors)
    return PC

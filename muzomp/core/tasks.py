# Create your tasks here
from __future__ import absolute_import, unicode_literals

from urllib.parse import unquote

import librosa
import numpy as np
from celery.task import task
from django.core.exceptions import ObjectDoesNotExist
from django.db import OperationalError
from django.utils import timezone

from .models import Audio, BPM

SUCCESS_CODE = 0
OBJECT_DOES_NOT_EXIST_ERROR_CODE = -9
UNKNOWN_PARAMETER_ERROR_CODE = -1
WRONG_ARRAY_LENGTH = -2
UNKNOWN_ERROR = -3
NUMBER_OF_SEGMENTS = 9804
LOST_TASK_TIMEOUT = 60


@task(name='core.tasks.process_bpm', autoretry_for=(OperationalError,))
def process_bpm(task_id):
    try:
        bpm = BPM.objects.get(id=task_id)
    except ObjectDoesNotExist:
        return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    if bpm.status == BPM.PROCESSED:
        return SUCCESS_CODE
    bpm.status = BPM.PROCESSING
    bpm.processing_start = timezone.now()
    bpm.save()
    y, sr = librosa.load(unquote(bpm.audio.file.url), offset=bpm.start_time, duration=bpm.duration)
    onset_env = librosa.onset.onset_strength(y, sr=sr)
    tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
    bpm.value = np.round(tempo, 1)
    bpm.status = BPM.PROCESSED
    bpm.processing_end = timezone.now()
    bpm.save()
    return SUCCESS_CODE


@task(name='core.tasks.schedule_bpm_tasks', autoretry_for=(OperationalError,))
def schedule_audio_tasks(audio_id):
    try:
        a = Audio.objects.get(id=audio_id)
    except ObjectDoesNotExist:
        return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    subtime = 15.0
    start_time = 0
    a.tasks_scheduled = a.duration // subtime
    a.save()
    while start_time < a.duration - subtime * 2:
        bpm = BPM.objects.create(audio=a, start_time=start_time, duration=subtime)
        bpm.save()
        process_bpm.delay(bpm.id)
        start_time = start_time + subtime
    last_duration = a.duration - (subtime * (a.tasks_scheduled - 1))
    bpm = BPM.objects.create(audio=a, start_time=start_time, duration=last_duration)
    bpm.save()
    process_bpm.delay(bpm.id)
    refresh_audio_status.delay(a.id)
    a.status = Audio.IN_QUEUE
    a.save()


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


@task(name='core.tasks.refresh_audio_status', autoretry_for=(OperationalError,))
def refresh_audio_status(audio_id):
    audio = Audio.objects.get(id=audio_id)
    bpm_tasks = BPM.objects.filter(audio=audio)
    processed = bpm_tasks.filter(status=BPM.PROCESSED)
    audio.tasks_scheduled = bpm_tasks.count()
    audio.tasks_processed = processed.count()

    if audio.tasks_scheduled == audio.tasks_processed:
        audio.status = Audio.PROCESSED
        merge.delay(audio_id, 'BPM')
        count_avg_bpm.delay(audio_id)
    elif audio.tasks_processed > 0:
        audio.status = Audio.PROCESSING
        refresh_audio_status.delay(audio_id)

    audio.save()


@task(name='core.tasks.count_avg_bpm')
def count_avg_bpm(audio_id):
    try:
        a = Audio.objects.get(id=audio_id)
    except ObjectDoesNotExist:
        return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    values = BPM.objects.filter(audio=a).order_by('start_time').values_list('value', flat=True)
    weights = list(BPM.objects.filter(audio=a).order_by('start_time').values_list('duration', flat=True))
    a.avg_bpm = sum(x * y for x, y in zip(weights, values)) / sum(weights)
    a.save()
    return SUCCESS_CODE


@task(name='core.tasks.get_principal_components')
def get_principal_components(files_list, variance_share):
    a = np.zeros(shape=(NUMBER_OF_SEGMENTS, len(files_list)), dtype=float)
    nf = 0
    for file in files_list:
        y, sr = librosa.load('music1/' + file, offset=15, duration=10)
        d = librosa.stft(y, n_fft=2048)
        x = np.abs(d)
        i = 0
        j = 0
        k = 0
        while i < 1026:
            while j < 430:
                s = 0
                for ii in range(i, i + 8):
                    for jj in range(j, j + 4):
                        s += x[ii][jj]
                a[k][nf] = s / 45
                k = k + 1
                j = j + 5
            j = 0
            i = i + 9
        nf = nf + 1
    means = np.mean(a, 1)
    stds = np.std(a, 1)
    for i in range(len(means)):
        a[i, :] = a[i, :] - means[i]
        a[i, :] = a[i, :] / stds[i]
    r = np.cov(a)
    d, v = np.linalg.eigh(r)

    component_number = 0  # number of principal components
    d = d[::-1]
    cumsum = np.cumsum(d)
    dsum = np.sum(d)
    for k in range(len(cumsum)):
        if cumsum[k] / dsum >= variance_share:
            component_number = k + 1
            break
    principal_vectors = np.zeros((NUMBER_OF_SEGMENTS, component_number))
    for k in range(component_number):
        principal_vectors[:, k] = v[:, NUMBER_OF_SEGMENTS - 1 - k]
    pc = np.dot(a.T, principal_vectors)
    print(pc)
    return pc


@task(name='core.tasks.calc_melody_components')
def calc_melody_components(principal_vectors, means, stds, filename, offset):
    y, sr = librosa.load(filename, offset=offset, duration=10)
    d = librosa.stft(y, n_fft=2048)
    x = np.abs(d)
    a = np.zeros(shape=(NUMBER_OF_SEGMENTS,), dtype=float)
    i = 0
    j = 0
    k = 0
    while i < 1026:
        while j < 430:
            s = 0
            for ii in range(i, i + 8):
                for jj in range(j, j + 4):
                    s += x[ii][jj]
            a[k] = s / 45
            k = k + 1
            j = j + 5
        j = 0
        i = i + 9
    for i in range(len(means)):
        a[i] = a[i] - means[i]
        a[i] = a[i] / stds[i]
    new_components = np.dot(a, principal_vectors)

    print(new_components)
    return new_components


@task(name='core.tasks.get_closest_melodies')
def get_closest_melodies(melody_components, pc, closest_count):
    component_number = melody_components.shape[1]
    num_of_melodies_in_db = pc.shape[0]
    dtype = np.dtype([('distance', float), ('number', int)])
    num_and_distance = np.array([], dtype=dtype)
    for i in range(num_of_melodies_in_db):
        distance = 0
        for j in range(component_number):
            distance = distance + (float(pc[i][j]) - melody_components[j]) * (
                    float(pc[i][j]) - melody_components[j])

        num_and_distance = np.insert(num_and_distance,
                                     num_and_distance.searchsorted(np.asarray((distance, i), dtype=dtype)),
                                     (distance, i))

    print(num_and_distance[:closest_count])
    return SUCCESS_CODE

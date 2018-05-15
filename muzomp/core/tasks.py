# Create your tasks here
from __future__ import absolute_import, unicode_literals

import hashlib
import json
from urllib.parse import unquote

import librosa
import numpy as np
from celery.task import task
from django.core.exceptions import ObjectDoesNotExist
from django.db import OperationalError
from django.utils import timezone

from .models import Audio, BPM, State

SUCCESS_CODE = 0
OBJECT_DOES_NOT_EXIST_ERROR_CODE = -9
UNKNOWN_PARAMETER_ERROR_CODE = -1
WRONG_ARRAY_LENGTH = -2
UNKNOWN_ERROR = -3
NUMBER_OF_SEGMENTS = 9804
NUMBER_OF_SEGMENTS_IN_TIME = 1026
NUMBER_OF_SEGMENTS_IN_FREQ = 430
TIME_STEP = 9
FREQ_STEP = 5
BPM_SPLIT_DURATION = 15.0
LOST_TASK_TIMEOUT = 60
HASHING_ALGORITHM = 'md5'


@task(name='core.tasks.process_bpm', autoretry_for=(OperationalError,))
def process_bpm(task_id):
    """
    Processes BPM task, setting value, status, processing_start and processing_end of core.models.BPM object

    :param task_id: task id
    :return: OBJECT_DOES_NOT_EXIST_ERROR_CODE if wrong audio_id specified, SUCCESS_CODE otherwise
    """
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


def split_duration(total_duration, target_duration, split_last=False):
    """
    Splits total_duration into parts
    :param total_duration: total duration of file
    :param target_duration: target duration of parts
    :param split_last: if True, last part may be less than others, otherwise it can be more that others
    :return: array of object with fields
        - start - start of part
        - end - end of part
        - duration - duration of part
        Note that the last part's duration will probably be not equal target_duration
    """
    res = []
    start = 0
    pre_end = total_duration - target_duration * 2
    total_count = total_duration // target_duration
    if split_last:
        pre_end = pre_end + target_duration
    while start < pre_end:
        res.append({'start': start, 'end': start + target_duration, 'duration': target_duration})
        start = start + target_duration
    if split_last:
        res.append({'start': start, 'end': start + target_duration, 'duration': target_duration})
        res.append({'start': start + target_duration, 'end': total_duration,
                    'duration': total_duration - target_duration * (total_count - 1)})
    else:
        res.append({'start': start, 'end': total_duration,
                    'duration': total_duration - target_duration * (total_count - 2)})
    return res


@task(name='core.tasks.schedule_bpm_tasks', autoretry_for=(OperationalError,))
def schedule_audio_tasks(audio_id):
    """
    Schedules all tasks related to specific audio:
        - refreshing principal components
        - BPMs
        - refresh audio status
    :param audio_id: core.models.Audio.id
    :return: OBJECT_DOES_NOT_EXIST_ERROR_CODE if wrong audio_id specified, SUCCESS_CODE otherwise
    """
    try:
        a = Audio.objects.get(id=audio_id)
    except ObjectDoesNotExist:
        return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    refresh_principal_components.delay(list(Audio.objects.all().values_list('id', flat=True)))
    intervals = split_duration(a.duration, BPM_SPLIT_DURATION)
    for interval in intervals:
        bpm = BPM.objects.create(audio=a, start_time=interval['start'], duration=interval['duration'])
        bpm.save()
        process_bpm.delay(bpm.id)
    refresh_audio_status.delay(a.id)
    a.status = Audio.IN_QUEUE
    a.save()
    return SUCCESS_CODE


@task(name='core.tasks.merge', autoretry_for=(OperationalError,))
def merge(audio_id):
    """
    Merges several BPM objects into one with extended duration
    :param audio_id: audio id to merge parameter for
    :return: OBJECT_DOES_NOT_EXIST_ERROR_CODE if wrong audio_id specified, SUCCESS_CODE otherwise
    """
    try:
        a = Audio.objects.get(id=audio_id)
    except ObjectDoesNotExist:
        return OBJECT_DOES_NOT_EXIST_ERROR_CODE
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


@task(name='core.tasks.refresh_audio_status', autoretry_for=(OperationalError,))
def refresh_audio_status(audio_id):
    """
    Refreshes audio status in case of long processing and schedules itself unless audio processing is finished
    :param audio_id: audio id to refresh status for
    :return: OBJECT_DOES_NOT_EXIST_ERROR_CODE if wrong audio_id specified, SUCCESS_CODE otherwise
    """
    try:
        audio = Audio.objects.get(id=audio_id)
    except ObjectDoesNotExist:
        return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    audio.tasks_scheduled = BPM.objects.filter(audio=audio).count()
    audio.tasks_processed = BPM.objects.filter(audio=audio, status=BPM.PROCESSED).count()

    if audio.tasks_scheduled == audio.tasks_processed:
        audio.status = Audio.PROCESSED
        merge.delay(audio_id)
        count_avg_bpm.delay(audio_id)
    elif audio.tasks_processed > 0:
        audio.status = Audio.PROCESSING
        refresh_audio_status.delay(audio_id)

    audio.save()
    return SUCCESS_CODE


@task(name='core.tasks.count_avg_bpm')
def count_avg_bpm(audio_id):
    """
    Calculates weighted BPM of audio after all parts are processed.
    :param audio_id: audio id to count avg_bpm for
    :return: OBJECT_DOES_NOT_EXIST_ERROR_CODE if wrong audio_id specified, SUCCESS_CODE otherwise
    """
    try:
        a = Audio.objects.get(id=audio_id)
    except ObjectDoesNotExist:
        return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    values = BPM.objects.filter(audio=a).order_by('start_time').values_list('value', flat=True)
    weights = list(BPM.objects.filter(audio=a).order_by('start_time').values_list('duration', flat=True))
    a.avg_bpm = sum(x * y for x, y in zip(weights, values)) / sum(weights)
    a.save()
    return SUCCESS_CODE


@task(name='core.tasks.refresh_principal_components')
def refresh_principal_components(audio_ids):
    """
    Computes principal components matrix for given list of audio ids and stores it in core.models.Global object
    :param audio_ids: list of audio ids to compute principal components for
    :return: SUCCESS_CODE
    """
    variance_share = 0.95
    files = list(Audio.objects.filter(id__in=audio_ids).values_list('file_url', flat=True))
    a = np.zeros(shape=(NUMBER_OF_SEGMENTS, len(files)), dtype=float)
    nf = 0
    for file in files:
        y, sr = librosa.load(file, offset=15, duration=10)
        d = librosa.stft(y, n_fft=2048)
        x = np.abs(d)
        i = 0
        j = 0
        k = 0
        while i < NUMBER_OF_SEGMENTS_IN_TIME:
            while j < NUMBER_OF_SEGMENTS_IN_FREQ:
                s = 0
                for ii in range(i, i + TIME_STEP-1):
                    for jj in range(j, j + FREQ_STEP):
                        s += x[ii][jj]
                a[k][nf] = s / (TIME_STEP*FREQ_STEP)
                k = k + 1
                j = j + FREQ_STEP
            j = 0
            i = i + TIME_STEP
        nf = nf + 1
    means = np.mean(a, 1)
    stds = np.std(a, 1)
    for i in range(len(means)):
        a[i, :] = a[i, :] - means[i]
        a[i, :] = a[i, :] / stds[i]
    r = np.cov(a)
    d, v = np.linalg.eigh(r)

    component_count = 0
    d = d[::-1]
    cumsum = np.cumsum(d)
    dsum = np.sum(d)
    for k in range(len(cumsum)):
        if cumsum[k] / dsum >= variance_share:
            component_count = k + 1
            break
    principal_vectors = np.zeros((NUMBER_OF_SEGMENTS, component_count))
    for k in range(component_count):
        principal_vectors[:, k] = v[:, NUMBER_OF_SEGMENTS - 1 - k]
    pc = np.dot(a.T, principal_vectors)
    h = hashlib.new(HASHING_ALGORITHM)
    h.update(audio_ids)
    State.objects.create(hash_id=h.hexdigest(),
                         pc=json.dumps(pc),
                         means=json.dumps(means),
                         stds=json.dumps(stds)).save()
    for i in range(pc.shape[0]):
        Audio.objects.filter(id=audio_ids[i]).update(principal_components=pc[i, :])
        get_closest_melodies.delay(audio_ids[i])
    return SUCCESS_CODE


@task(name='core.tasks.calc_melody_components')
def calc_melody_components(audio_id, offset, audio_ids=None):
    """
    Computes components for new audio based on existing state described by audio_ids
    :param audio_id: audio id to calculate principal vector for
    :param offset: offset for calculating components in audio
    :param audio_ids: ids to use for principal components matrix
    :return:
    """
    if audio_ids is None:
        state = State.objects.latest('calculated_date')
    else:
        try:
            h = hashlib.new(HASHING_ALGORITHM)
            h.update(audio_ids)
            state = State.objects.get(hash_id=h.hexdigest())
        except ObjectDoesNotExist:
            return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    means = state.means
    stds = state.stds
    principal_vectors = state.pc
    audio = Audio.objects.get(id=audio_id)
    y, sr = librosa.load(unquote(audio.file.url), offset=offset, duration=10)
    d = librosa.stft(y, n_fft=2048)
    x = np.abs(d)
    a = np.zeros(shape=(NUMBER_OF_SEGMENTS,), dtype=float)
    i = 0
    j = 0
    k = 0
    while i < NUMBER_OF_SEGMENTS_IN_TIME:
        while j < NUMBER_OF_SEGMENTS_IN_FREQ:
            s = 0
            for ii in range(i, i + TIME_STEP-1):
                for jj in range(j, j + FREQ_STEP-1):
                    s += x[ii][jj]
            a[k] = s / (TIME_STEP*FREQ_STEP)
            k = k + 1
            j = j + FREQ_STEP
        j = 0
        i = i + TIME_STEP
    for i in range(len(means)):
        a[i] = a[i] - means[i]
        a[i] = a[i] / stds[i]
    new_components = np.dot(a, principal_vectors)
    Audio.objects.filter(id=audio_id).update(principal_components=new_components)
    return SUCCESS_CODE


@task(name='core.tasks.get_closest_melodies')
def get_closest_melodies(audio_id, audio_ids=None):
    """
    Returns closest audios with distance according to its' principal components
    :param audio_id: target audio to compare others to
    :param audio_ids: audio ids to compare audio to
    :return:
    """
    if audio_ids is None:
        state = State.objects.latest('calculated_date')
    else:
        try:
            h = hashlib.new(HASHING_ALGORITHM)
            h.update(audio_ids)
            state = State.objects.get(hash_id=h.hexdigest())
        except ObjectDoesNotExist:
            return OBJECT_DOES_NOT_EXIST_ERROR_CODE
    pc = state.pc
    melody_components = Audio.objects.get(id=audio_id).principal_components
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

    Audio.objects.filter(id=audio_id).update(closest_list=json.dumps(num_and_distance))
    return SUCCESS_CODE

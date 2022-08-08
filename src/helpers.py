import json
import os
import platform
import subprocess as sp
from getpass import getpass
from typing import Any, Iterable


is_wt = os.environ.get('WT_PROFILE_ID') != None # windows terminal
is_linux = platform.system() == 'Linux'
is_win = platform.system() == 'Windows'


def probe(file_path: str) -> dict:

    cmd = ("ffprobe",
           "-v", "error",
           "-of", "json",
           "-show_format",
           "-show_streams",
           file_path)

    data = json.loads(sp.check_output(cmd))

    # common values
    data.update({'stream':   data['streams'][0],
                 'fps':      round(eval(data['streams'][0]['avg_frame_rate'])),
                 'duration': data['format']['duration'],
                 'res':      (data['streams'][0]['width'], data['streams'][0]['height']),
                 'codec':    data['streams'][0]['codec_name']})

    data.pop('streams') # we only need the first stream

    return data


def check_os():
    if platform.architecture()[0] != '64bit':
        raise OSError('Smoothie is only compatible with 64bit systems.')

    if platform.system() not in ('Linux', 'Windows'):
        raise OSError(f'Unsupported OS "{platform.system()}"')


def pause():
    getpass('Press enter to continue..')


def literal_path(p: str):
    return os.path.abspath(os.path.expanduser(os.path.expandvars(p)))


def next_in(i: Iterable, idx: int, default: Any = ''):
    try:
        return i[idx + 1]
    except IndexError:
        return default


def timecode_to_sec(timecode: str) -> float:
    times = timecode.split(':')
    if len(times) == 1:
        return float(times[0])
    if len(times) == 2:
        return float(times[0]) * 60 + float(times[1])
    else:
        return float(times[0]) * 3600 + float(times[1]) * 60 + float(times[2])


def ff_stdout_to_dict(line: str) -> dict:
    """
    parse ffmpeg output to a dict

    only works when -progress was specified
    """

    data = {}
    pairs = line.strip().splitlines()
    for pair in pairs:
        key, value = pair.split('=')
        value = float(value) if value.isdigit() else value
        data[key] = value

    return data


# Bool aliases
yes = 'true', 'yes', 'y', '1', True
no = 'false', 'no', 'n', '0', 'null', '', None, False


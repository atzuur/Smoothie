import json
import os
import platform
import subprocess as sp
from getpass import getpass
from typing import Any, Iterable

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

    data.pop('streams')  # we only need the first stream

    return data


def check_os() -> None:
    if platform.architecture()[0] != '64bit':
        raise OSError('This script is only compatible with 64bit systems.')

    if platform.system() not in ('Linux', 'Windows'):
        raise OSError(f'Unsupported OS "{platform.system()}"')


def pause() -> None:
    getpass('Press enter to continue..')


def expand_path(p: str) -> str:
    return os.path.expanduser(os.path.expandvars(p))


def next_in(i: Iterable, idx: int, default: Any = '') -> Any:
    try:
        return i[idx + 1]
    except IndexError:
        return default


def timecode_to_sec(timecode: str) -> float:
    times = [float(t) for t in timecode.split(':')]
    match len(times):
        case 0:
            return 0
        case 1:
            return times[0]
        case 2:
            return times[0] * 60 + times[1]
        case 3:
            return times[0] * 3600 + times[1] * 60 + times[2]
        case _:
            raise ValueError(f'Invalid timecode: "{timecode}"')


def ff_stdout_to_dict(line: str) -> dict:
    """
    parse ffmpeg output to a dict

    only works when `-progress` was specified
    """

    data = {}
    pairs = line.strip().splitlines()
    for pair in pairs:
        key, value = pair.split('=')
        value = float(value) if value.isdigit() else value
        data[key] = value

    data['out_time'] = data['out_time'][:-4]  # remove trailing zeros

    return data


def dict_to_kwarg_string(d: dict) -> str:
    return ', '.join(f'{key}={value}' for key, value in d.items())


# bool aliases
yes = 'true',  'yes', 'y', '1', True
no = 'false', 'no',  'n', '0', 'null', '', None, False

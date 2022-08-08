import random
import subprocess as sp
import sys
from argparse import Namespace
from glob import glob
from os import get_terminal_size, path
from pprint import pformat

from constants import FRUITS
from helpers import *
from parse import parse_conf
from plugins.colors import create_bar, fg, reset


def main(args: Namespace):

    input_files = expand_input_files(args.input)

    if args.config:
        config_filepath = args.config
    else:
        config_filepath = path.join(sys.path[0], '../settings/recipe.yaml')

    if not path.exists(config_filepath):
        raise FileNotFoundError(f'Config filepath does not exist: "{config_filepath}"')

    conf = parse_conf(config_filepath)

    if args.override:
        for override in args.override:
            try:
                category, pair = args.override.split(';')
                key, value = pair.split('=')
                conf[category][key] = value
            except ValueError:
                raise ValueError(f'Invalid override format: "{override}"')

    if mask := conf['flowblur']['mask'] not in no:

        if not path.splitext(mask)[1]:
            mask += '.png'

        default_path = path.abspath(path.join(sys.path[0], f'../masks/{mask}'))

        if path.abspath(mask) == mask:
            conf['flowblur']['mask'] = mask
        else:
            conf['flowblur']['mask'] = default_path

        if not path.exists(conf['flowblur']['mask']):
            raise FileNotFoundError(f'Mask filepath does not exist: "{conf["flowblur"]["mask"]}"')
            

    for video in input_files:

        if args.trim:

            args.trim = args.trim.strip().replace(' ', '')

            try:
                fro, to = args.trim.split('-')
            except ValueError: # if there is no '-' in the string
                raise ValueError(f'Invalid trim format: "{args.trim}"')

            try:
                fro = int(fro)
                to = int(to)
            except ValueError: # if not an int (frame), then it's a timecode
                fro = timecode_to_sec(fro)
                to = timecode_to_sec(to)

                fps = probe(video)['fps']
                fro = int(fro * fps)
                to = int(to * fps)

            if fro > to:
                raise ValueError(f'Trim end cannot be before trim start: {fro=}-{to=}')
            elif fro == to:
                raise ValueError(f'Trim start and end cannot be the same: {fro=}-{to=}')

            conf['trim'] = {'start': fro, 'end': to}

        out_name = get_output_file(video, conf)

        if args.output:
            if len(input_files) > 1:
                output_file = path.join(args.output, out_name)
            else:
                output_file = args.output
        else:
            output_file = path.join(path.dirname(video), out_name)
            if args.peek: output_file = path.splitext(output_file)[0] + '.png'

        if path.exists(output_file):
            print(f'Skipping {video} (already exists)')
            continue

        vpy = path.abspath(path.join(sys.path[0], 'vitamix.vpy'))
        if not path.exists(vpy):
            raise FileNotFoundError(f'Vpy script could not be found: "{vpy}"')

        vs_cmd = ['vspipe',
                  vpy,
                  '-a', f'input_file="{video}"',
                  '-a', f'config_file="{conf}"']

        ff_cmd = ['ffmpeg',
                  '-hide_banner',
                  '-v', 'error',
                  '-progress', '-', # easier to parse progress info
                  '-stats_period', '0.05',
                  '-i', '-']

        if args.peek:
            vs_cmd += '--start', args.peek, '--end', args.peek
            ff_cmd += f'"{output_file}"'

        else:
            # map the audio from the input to the output, linux needs an escape character
            audio = ['-map', '0:v', '-map', '1:a?'] if is_win else ['-map', '0:v', '-map', '1:a\?']

            ts = conf['timescale']['in'] * conf['timescale']['out']
            if ts != 1:
                audio += '-af', f'atempo={ts}' # sync audio

            # these need to be added separately so that they extend properly
            ff_cmd += '-i', f'"{video}"',
            ff_cmd += audio
            ff_cmd += conf["encoding"]["args"].split(' ')
            ff_cmd.append(f'"{output_file}"')

        vs_cmd += ['-'] # output to stdin

        run_blend_cmds(vs_cmd, ff_cmd, video)


def expand_input_files(files: list):
    expanded = []
    for file in files:
        expanded += glob(file, recursive=True)

    return [literal_path(file) for file in expanded]


def get_output_file(input_file: str, conf: dict):

    if not conf['output file']['prefix']: prefix = ''
    video_name = prefix + path.basename(input_file)

    cont = conf['output file']['container']
    if cont in no:
        ext = '.mp4'
    else:
        ext = cont if cont.startswith('.') else '.' + cont

    suffix = conf['output file']['suffix'].casefold()

    if suffix == 'fruits':
            suffix = random.choice(FRUITS)

    elif suffix == 'detailed':
        suffix = ''
        if conf['interpolation']['enabled']:
            suffix += f"{conf['interpolation']['fps']}fps"
        if conf['frame blending']['enabled']:
            suffix += f" - {conf['frame blending']['output fps']} @ {float(conf['frame blending']['intensity'])}"
        if conf['flowblur']['enabled']:
            suffix += f", fb @ {conf['flowblur']['amount']}"

    else: suffix = 'Smoothie'

    return f'{video_name} ~ {suffix}{ext}'


def run_blend_cmds(vs_cmd: list, ff_cmd: list, video: str):

    vs_proc = sp.Popen(vs_cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    ff_proc = sp.Popen(ff_cmd, stdin=vs_proc.stdout, stdout=sp.PIPE, stderr=sp.PIPE)

    video_data = probe(video)

    while (vs_proc.poll() is None and
           ff_proc.poll() is None):

        if not ff_proc.stdout: continue

        for line in ff_proc.stdout:

            ff_data = ff_stdout_to_dict(line)

            perc = ff_data['frame'] / video_data['duration'] * video_data['fps']
            barsize = int(get_terminal_size().columns / 2)

            progress = perc * barsize
            perc *= 100

            bar = create_bar(barsize, progress=progress, arrow=('━' ,'▶'))

            sep = fg.gray + '|' + fg.lwhite
            key = lambda k: k + fg.gray + ':' + ff_data[k]

            info = f'{fg.lwhite}{path.basename(video)} {sep} {key("time")} {sep} {key("speed")} {sep} {perc:.2f}{fg.gray}% {reset}'

            print('\033[0K', end='') # clear the line
            print('\033[F', end='') # move cursor up one line
            print('\033[0K', end='') # clear the line again

            print(info)
            print(bar)

    if vs_proc.poll():
        tb = '\n'.join([line.decode('utf-8').strip('\n') for line in vs_proc.stderr.readlines()])
        raise RuntimeError(f'\n {pformat(" ".join(vs_cmd))} \n\n VSPipe failed: \n {tb}')

    elif ff_proc.poll():
        tb = '\n'.join([line.decode('utf-8').strip('\n') for line in ff_proc.stderr.readlines()])
        raise RuntimeError(f'\n {pformat(" ".join(ff_cmd))} \n\n FFmpeg failed: \n {tb}')

    else:
        print(f'{fg.green}Smoothie - finished blending {path.basename(video)}{reset}')

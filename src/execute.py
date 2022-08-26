import io
import random
import subprocess as sp
import sys
from argparse import Namespace
from glob import glob
from os import get_terminal_size, path

import colors

import const
import script
from helpers import *
from parse import parse_conf


def main(args: Namespace):

    input_files = expand_input_files(args.input)

    if args.config:
        config_filepath = args.config
    else:
        config_filepath = path.join(sys.path[0], '../settings/recipe.yaml')

    if not path.exists(config_filepath):
        raise FileNotFoundError('Config filepath does not exist: '
                                f'"{config_filepath}"')

    conf = parse_conf(config_filepath)

    if args.override:
        for override in args.override:
            try:
                category, pair = override.split(';')
                key, value = pair.split('=')
                conf[category][key] = value
            except ValueError:
                raise ValueError(f'Invalid override format: "{override}"')

    if (flbmask := conf['flowblur']['mask']) not in no:
        conf['flowblur']['mask'] = get_mask_directory(flbmask)

    if (imask := conf['interpolation']['mask']) not in no:
        conf['interpolation']['mask'] = get_mask_directory(imask)

    for video in input_files:

        out_name = get_output_file(video, conf)

        if args.output:
            if len(input_files) > 1:
                output_file = path.join(args.output, out_name)
            else:
                output_file = args.output

        elif fold := conf['output file']['folder']:
            output_file = path.join(fold, out_name)

        else:
            output_file = path.join(path.dirname(video), out_name)
            if args.peek:
                output_file = path.splitext(output_file)[0] + '.png'

        if path.exists(output_file):
            colors.printp(f'Skipping {video} (already exists)', 'info')
            continue

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


        vpy_path, vpy_contents = script.generate(conf, video)
        with open(vpy_path, 'w') as f:
            f.write(vpy_contents)

        vs_cmd = ['vspipe',
                  vpy_path,
                  '-c', 'y4m']

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
            # map the audio from the input to the output
            audio = ['-map', '0:v', '-map', '1:a?']

            if (ts := conf['timescale']['in'] * conf['timescale']['out']) != 1:
                audio += '-af', f'atempo={ts}' # sync audio

            # these need to be added separately so that they extend properly
            ff_cmd += '-i', video,
            ff_cmd += audio
            ff_cmd += conf['encoding']['args'].split(' ')
            ff_cmd.append(f'"{output_file}"')

        vs_cmd += ['-'] # output to stdin

        run_blend_cmds(vs_cmd, ff_cmd, video)


def run_blend_cmds(vs_cmd: list, ff_cmd: list, video: str):


    vs_proc = sp.Popen(vs_cmd, stdout=sp.PIPE, stderr=sp.PIPE)

    ff_proc = sp.Popen(ff_cmd, stdin=vs_proc.stdout,
                       stdout=sp.PIPE, stderr=sp.PIPE)

    video_data = probe(video)

    while (vs_proc.poll() is None and
           ff_proc.poll() is None):

        if not ff_proc.stdout:
            continue

        for line in ff_proc.stdout:

            ff_data = ff_stdout_to_dict(line)

            perc = ff_data['frame'] / (video_data['duration'] * video_data['fps'])
            barsize = int(get_terminal_size().columns / 2)

            progress = perc * barsize
            perc *= 100

            bar = colors.create_bar(barsize,
                                    progress=progress,
                                    arrow=('━', '▶'))

            sep = colors.fg.grey + '|' + colors.fg.lwhite
            key = lambda k: k + colors.fg.grey + ':' + ff_data[k]

            # video.mkv | time: 00:00:25.84 | speed: 0.16x | 74.2%
            info = (colors.fg.lwhite +
                    path.basename(video) + sep +
                    key("time") + sep +
                    key("speed") + sep +
                    round(perc, 1) +
                    colors.fg.grey + '%' +
                    colors.reset)

            print('\033[0K', end='') # clear the line
            print('\033[F', end='') # move cursor up one line
            print('\033[0K', end='') # clear the line again

            print(info)
            print(bar)

    if vs_proc.poll():

        tb = '\n'.join([line.decode('utf-8').strip('\n')
                       for line in vs_proc.stderr.readlines()])

        raise RuntimeError(f'\n{" ".join(vs_cmd)}\n\n'
                           f'VSPipe failed:\n {tb}')

    elif ff_proc.poll():

        tb = '\n'.join([line.decode('utf-8').strip('\n')
                       for line in ff_proc.stderr.readlines()])

        raise RuntimeError(f'\n{" ".join(ff_cmd)}\n\n' 
                           f'FFmpeg failed:\n {tb}')

    else:
        print(f'{colors.fg.green}'
              f'Smoothie - finished blending {path.basename(video)}'
              f'{colors.reset}')


def expand_input_files(files: list):
    expanded = []
    for file in files:
        expanded += glob(file, recursive=True)

    return [path.abspath(file) for file in expanded]


def get_output_file(input_file: str, conf: dict):

    if not conf['output file']['prefix']:
        prefix = ''
    video_name = prefix + path.basename(input_file)

    cont = conf['output file']['container']
    if cont in no:
        ext = '.mp4'
    else:
        ext = cont if cont.startswith('.') else '.' + cont

    suffix = conf['output file']['suffix'].casefold()

    if suffix == 'fruits':
        suffix = random.choice(const.FRUITS)

    elif suffix == 'detailed':
        suffix = ''
        if conf['interpolation']['enabled']:
            suffix += f"{conf['interpolation']['fps']}fps"
        if conf['frame blending']['enabled']:
            suffix += f" - {conf['frame blending']['output fps']} @ {float(conf['frame blending']['intensity'])}"
        if conf['flowblur']['enabled']:
            suffix += f", fb @ {conf['flowblur']['amount']}"

    else:
        suffix = 'Smoothie'

    return f'{video_name} ~ {suffix}{ext}'


def get_mask_directory(mask: str):

    mask_dir = ''
    default_dir = path.abspath(path.join(sys.path[0], f'../masks'))

    if path.abspath(mask) == mask: # if it's already an absolute path
        mask_dir = mask

    if not path.splitext(mask)[1]:

        for ext in const.IMAGE_EXTS:
            if path.exists(file := path.join(default_dir, mask + ext)):
                mask_dir = file
                break

    if not path.exists(mask_dir):
        raise FileNotFoundError(f'Mask filepath does not exist: "{mask}"')

    return mask_dir

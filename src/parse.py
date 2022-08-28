from ast import literal_eval

import yaml

import weighting
from helpers import *
from const import ENC_PRESETS


def parse_conf(file_path: str) -> dict:

    with open(file_path, 'r') as f:
        conf = yaml.safe_load(f)

    weight_func, params = parse_weights(conf['frame blending']['weighting'])

    conf['frame blending']['weight func'] = weight_func
    conf['frame blending']['weight params'] = params

    conf['encoding']['args'] = parse_ez_enc_args(conf['encoding']['args'])

    return conf


def parse_weights(orig: str | list) -> tuple[str, dict]:

    if not orig:
        raise ValueError('no weights given')

    if isinstance(orig, list):
        return 'divide', {'weights': orig}

    else:
        orig = orig.replace(' ', '')
        orig = orig.split('|')
        func_name = orig[0]

        if not hasattr(weighting, func_name):
            raise ValueError(f'Invalid weighting function: "{func_name}"')

        if len(orig) == 1:
            return func_name, {}

        else:
            params = {}
            for pair in orig[1].split(';'):
                param, value = pair.split('=')
                # custom func is a string that literal_eval can't parse
                if not (func_name == 'custom' and param == 'func'):
                    try:
                        value = literal_eval(value)
                    except ValueError as v:
                        raise ValueError(f'weighting: invalid value "{value}" '
                                         f'for parameter "{param}"') from v

                params[param] = value

            return func_name, {**params}


def parse_ez_enc_args(args: str) -> str:

    args = args.strip().casefold().split(' ')

    for i, word in enumerate(args):

        if 'x26' in word: # x265 or x264
            args[i] = ENC_PRESETS['h26' + word[3]]['cpu'] + ' -c:a copy'

        elif (std := word) in ENC_PRESETS: # valid standard
            if (enc := next_in(args, i)) in ENC_PRESETS[std]: # valid encoder
                args[i] = ENC_PRESETS[std][enc] + ' -c:a copy'
                args.pop(i + 1)

        if word == 'upscale':
            args.insert(i, '-vf scale=-2:2160:flags=neighbor')
            if 'yuv420p10le' not in ''.join(args):
                args[i] += ' -pix_fmt yuv420p10le'
            args.pop(i + 1)

    return ' '.join(args)

from colors import printp

from helpers import no, yes, dict_to_kwarg_string


def generate(conf: dict, input_video: str) -> str:

    def verb(msg: str):
        if conf['misc']['verbose']:
            printp(msg, 'info')

    script = ['import havsfunc as haf',
              'import vapoursynth as vs',
              'import vsutil',
              'import filldrops',
              'import weighting',
              'core = vs.core',
              f'video = core.bs.VideoSource("{input_video}")']

    if 'trim' in conf:
        script.append(f'video.std.Trim({conf["trim"]["start"]}, {conf["trim"]["end"]})')

    if (ts := conf['timescale']['in']) != 1: # input timescale, done before interpolation
        script.append(f'video.std.AssumeFPS(fpsnum=(1 / {ts} * video.fps))')

    if conf['interpolation']['enabled'] in yes:

        script.extend([f'video = vsutil.depth(video, 8)', # svpflow needs 8-bit input
                        'original = video',
                       f'if (interp := {conf["interpolation"]["fps"]}).endswith("x"): '
                        'interp_fps = int(video.fps * interp.replace("x", ""))',
                       f'else: interp_fps = {conf["interpolation"]["fps"]}',

                        'video = haf.InterFrame(video, '
                       f'GPU={conf["interpolation"]["gpu"] in yes}, '
                        'NewNum=interp_fps, '
                       f'Preset="{conf["interpolation"]["speed"]}", '
                       f'Tuning="{conf["interpolation"]["tuning"]}", '
                       f'OverrideAlgo="{conf["interpolation"]["algorithm"]})"'])

        if (mask := conf['interpolation']['mask']) not in no:

            verb(f'Masking interpolation with "{mask}"')

            script.extend([f'rmask = core.bs.VideoSource({mask})',
                           f'fmask = rmask.std.Minimum().std.BoxBlur(vradius=6, radius=6, passes=2)',
                           f'video = original.std.MaskedMerge(video, feathered_mask)'])

    # output timescale, done after interpolation
    if (ts := conf['timescale']['out']) != 1:
        script.append(f'video.std.AssumeFPS(fpsnum=video.fps * {ts})')

    if (thr := conf['misc']['dedup threshold']) not in no:
        script.append(f'video = filldrops.FillDrops(video, thresh={thr})')

    if (blnd := conf['frame blending'])['enabled'] in yes:

        verb(f'Getting weight vector with call '
             # gaussian(frames=15, apex=1.5, std_dev=4)
             f'`{blnd["weight func"]}({dict_to_kwarg_string(blnd["weight params"])})`')

        script.extend([f'blended_frames = int(video.fps / '
                       f'{blnd["output fps"]} * '
                       f'{blnd["intensity"]})'

                       f'weights = weighting.{blnd["weight func"]}'
                       f'(blended_frames, **{blnd["weight params"]})',

                       f'video.frameblender.FrameBlend(weights)',
                       f'video = haf.ChangeFPS(video, {blnd["output fps"]})'])

    if conf['flowblur']['enabled'] and conf['flowblur']['amount'] not in no:

        verb(f'Getting motion vectors for FlowBlur (amount: {conf["flowblur"]["amount"]}')

        script.extend(['original = video',
                       'super_c = core.mv.Super(video, 16, 16, rfilter=3)',
                       'bwd_vec = core.mv.Analyse(super, isb=True, blksize=16, plevel=2, dct=5)',
                       'fwd_vec = core.mv.Analyse(super, blksize=16, plevel=2, dct=5)',

                       'video.mv.FlowBlur(video, '
                       'super=super_c, '
                       'mvbw=bwd_vec, '
                       'mvfw=fwd_vec, '
                      f'blur={conf["flowblur"]["amount"]})'])

        if (mask := conf['flowblur']['mask']) not in no:

            verb(f'Masking FlowBlur with "{mask}"')

            script.extend([f'rmask = core.bs.VideoSource({mask})',
                           f'fmask = rmask.std.Minimum().std.BoxBlur(vradius=6, radius=6, passes=2)',
                           f'video = original.std.MaskedMerge(video, feathered_mask)'])

    script.append('video.set_output()')

    return '; '.join(script)

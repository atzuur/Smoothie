import vapoursynth as vs

m: vs.VideoNode
m = vs.core.imwri.Read('/home/atzur/gh/Smoothie/masks/cian.png')
m.std.Minimum().std.BoxBlur(vradius=6, vpasses=2, hradius=6, hpasses=2)

vs.core.imwri.Write(m, 'PNG', '/home/atzur/gh/Smoothie/masks/cian%d.png')

m.set_output()
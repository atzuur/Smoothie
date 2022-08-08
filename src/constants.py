ENC_PRESETS = {
    'h264': {
        'nvenc':     "-c:v h264_nvenc -preset p7 -rc vbr -b:v 250M -cq 18",
        'amf':       "-c:v h264_amf -quality quality -qp_i 16 -qp_p 18 -qp_b 22",
        'quicksync': "-c:v h264_qsv -preset veryslow -global_quality:v 15",
        'cpu':       "-c:v libx264 -preset slow -aq-mode 3 -crf 18"
    },
    'h265': {
        'nvenc':     "-c:v hevc_nvenc -preset p7 -rc vbr -b:v 250M -cq 20 -pix_fmt yuv420p10le",
        'amf':       "-c:v hevc_amf -quality quality -qp_i 18 -qp_p 20 -qp_b 24 -pix_fmt yuv420p10le",
        'quicksync': "-c:v hevc_qsv -preset veryslow -global_quality:v 18 -pix_fmt yuv420p10le",
        'cpu':       "-c:v libx265 -preset medium -x265-params aq-mode=3:no-sao=1 -crf 20 -pix_fmt yuv420p10le"
    }
}

FRUITS = 'Berry',     'Cherry',  'Cranberry',  'Coconut',     'Kiwi',      \
         'Avocado',   'Durian',  'Lemon',      'Dragonfruit', 'Fig',       \
         'Mirabelle', 'Banana',  'Pineapple',  'Pitaya',      'Blueberry', \
         'Raspberry', 'Apricot', 'Strawberry', 'Melon',       'Papaya',    \
         'Apple',     'Pear',    'Orange',     'Mango',       'Plum',      \
         'Peach',     'Grape',   'Clementine', 'Lingonberry', 'Lime'

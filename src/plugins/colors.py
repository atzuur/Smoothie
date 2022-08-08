import os
from dataclasses import dataclass
from itertools import chain
from types import TracebackType
from typing import Iterable

os.system('') # required for conhost

eof = eol = end = reset = '\33[0m'

# * == incompatible with windows
# ** == incompatible with conhost (works in vscode terminal etc)

class Style:
    bold      = '\33[1m' # **
    italic    = '\33[3m' # **
    url       = '\33[4m'
    blink     = '\33[5m' # *
    altblink  = '\33[6m' # *
    selected  = '\33[7m'
    invisible = '\33[8m'
    strike    = '\33[9m' # **


class Foreground:
    rgb = lambda r, g, b: f'\33[38;2;{r};{g};{b}m'
    black    = '\33[30m'
    red      = '\33[31m'
    green    = '\33[32m'
    yellow   = '\33[33m'
    blue     = '\33[34m'
    violet   = '\33[35m'
    beige    = '\33[36m'
    white    = '\33[37m'
    grey     = '\33[90m'
    lred     = '\33[91m'
    lgreen   = '\33[92m'
    lyellow  = '\33[93m'
    lblue    = '\33[94m'
    lviolet  = '\33[95m'
    lbeige   = '\33[96m'
    lwhite   = '\33[97m'


class Background:
    rgb = lambda r, g, b: f'\33[48;2;{r};{g};{b}m'
    black    = '\33[40m'
    red      = '\33[41m'
    green    = '\33[42m'
    yellow   = '\33[43m'
    blue     = '\33[44m'
    violet   = '\33[45m'
    beige    = '\33[46m'
    white    = '\33[47m'
    grey     = '\33[100m'
    lred     = '\33[101m'
    lgreen   = '\33[102m'
    lyellow  = '\33[103m'
    lblue    = '\33[104m'
    lviolet  = '\33[105m'
    lbeige   = '\33[106m'
    lwhite   = '\33[107m'

# aliases
fg = Foreground
bg = Background
st = Style


@dataclass
class RGB(tuple):

    def __new__(cls, R: int, G: int, B: int):
        return super().__new__(cls, (R, G, B))

    def __init__(self, R: int, G: int, B: int):

        self.R = int(R)
        self.G = int(G)
        self.B = int(B)

        if not self.validate():
            raise ValueError('RGB values must be between 0 and 255')

    def __str__(self):
        return f'({self.R}, {self.G}, {self.B})'

    def __repr__(self):
        return f'RGB{str(self)}'

    def __len__(self):
        return 3

    def validate(self):
        return (self.R >= 0 and self.R <= 255 and
                self.G >= 0 and self.G <= 255 and
                self.B >= 0 and self.B <= 255)


def printp(text, preset: str, printend: str = '\n', **kwargs):

    """
    wrapper function for printing stuff with presets

    args:
        text: Any - text to print
        preset: str - preset name
            presets:
                `rainbow`, `syntax_hl`, `warning`, `error`,
                `success`, `info`, `debug`, `exception`

        printend: str - end of line character    

    all kwargs are passed to the preset function, see implementation for details
    """

    preset = preset.casefold()

    if preset == 'rainbow':
        print(rainbow_txt(text, **kwargs))

    elif preset == 'syntax_hl':
        print(syntax_hl(text))

    elif preset == 'warning':
        print(prfx_txt(text, 'WARNING',
                       prfx_color=fg.yellow,
                       text_color=fg.yellow),
                       end=printend)

    elif preset == 'error':
        print(prfx_txt(text, 'ERROR',
                       prfx_color=fg.red,
                       text_color=fg.lred),
                       end=printend)

    elif preset == 'success':
        print(prfx_txt(text, 'SUCCESS',
                       prfx_color=fg.lgreen,
                       text_color=fg.green),
                       end=printend)

    elif preset == 'info':
        print(prfx_txt(text, 'INFO',
                       prfx_color=fg.blue,
                       text_color=fg.white),
                       end=printend)

    elif preset == 'debug':
        print(prfx_txt(text, 'DEBUG',
                       prfx_color=fg.lyellow,
                       text_color=fg.white),
                       end=printend)

    elif preset == 'exception':
        print(exc_format(text, **kwargs), end=printend)

    else:
        print(text, end=printend)


def rainbow_txt(text: str, *, density=1, affect='fg') -> str:

    text = list(text)
    # split text into groups of length n (density)
    text = [text[i:i + density] for i in range(0, len(text), density)]

    if affect == 'fg': c = Foreground
    elif affect == 'bg': c = Background
    else: raise ValueError(f'affect must be either "fg" or "bg", got "{affect}"')

    for (idx, char), vals in zip(enumerate(text), gen_rainbow(len(text))):

        if len(char) > 1: # if char is a list of characters
            for i, subchar in enumerate(char):
                text[idx][i] = c.rgb(*vals) + subchar # apply the current color to each subchar

        else:
            text[idx] = c.rgb(*vals) + ''.join(char) # char can be list with 1 character

    return ''.join(chain.from_iterable(text)) + reset # flatten + reset


def prfx_txt(text: str,
             prefix: str, *,
             prfx_color: str = fg.lwhite, prfx_style: str = st.url,
             text_color: str = fg.white, text_style: str = '',
             separator: str = ' >>> ') -> str:

    """
    add a prefix to string

    "text" -> f"[{prefix}] >>> text"
    """

    fmt_prefix = fg.white + '[' + prfx_color + prfx_style + prefix + reset + fg.white + ']'

    if len(t := text.strip().splitlines()) > 1: # if multiline string
        s = fmt_prefix + '\n'
        for line in t:
            s += separator + text_color + text_style + line + '\n' + reset
    else:
        s = fmt_prefix + separator + text_color + text_style + text

    return s.rstrip(reset + '\n') + reset # strip last newline


def exc_format(exc: BaseException | str, *,
               msg: str = None,
               extra_tb: TracebackType | str = None) -> str:
    """
    pip-style exception formatting

    args:
        exc: BaseException | str - exception to format
        msg: str - message to print before exception
        extra_tb: TracebackType | str - extra traceback to print above the exception
    """
    import traceback

    if msg is None:
        exctype = exc.__class__.__name__ if isinstance(exc, BaseException) else str(exc)
        msg = f'{fg.yellow}{exctype}{fg.white} occurred, printing traceback...'

    formatted = []

    if extra_tb is not None:
        if isinstance(extra_tb, TracebackType):
            formatted += ''.join(traceback.format_tb(extra_tb)).splitlines()
        else:
            formatted += str(extra_tb).splitlines()

    if isinstance(exc, BaseException):
        formatted += ''.join(traceback.format_exception(exc)).splitlines()
    else:
        formatted += [exc]

    pad = ' ' * 4 # hardcoded pad because idk how f-string padding works :c

    result = f"""
{fg.red}×{reset} {msg}
{fg.red}╰─> {fg.white}[{fg.red}{len(formatted)} line(s) of output{fg.white}]\n
"""
    for line in formatted: result += pad + line + '\n'

    result += f'\n{pad}[{fg.red}end of output{fg.white}]'

    return result + '\n'


def syntax_hl(text: str) -> str:

    """
    highlight special characters in text
    pink theme :3
    """

    parens = ('(', ')', '{', '}', '[', ']')

    ops = ('+', '-', '/', '\\',
           '%', '=', '&', '$',
           '@', '?', '|', '<',
           '>', '*', '!', '~', '^')

    delims = (',', '.', ':', ';')

    default = '\033[38;5;189m'

    fmt = lambda char, *rgb: fg.rgb(*rgb) + char + reset

    hl = list(text)

    for idx, char in enumerate(hl):

        if char.isdigit():   hl[idx] = fmt(char, 255, 168, 227)
        elif char in parens: hl[idx] = fmt(char, 140, 190, 178)
        elif char in ops:    hl[idx] = fmt(char, 195, 117, 243)
        elif char in delims: hl[idx] = fmt(char, 156, 191, 255)

        else: hl[idx] = default + char + reset

    return ''.join(hl) + reset


def hsv_to_rgb(h: float, s: float, v: float) -> RGB:

    if s == 0.0: return v, v, v

    i = int(h * 6)
    f = h * 6 - i

    p = int(255 * (v * (1 - s )))
    q = int(255 * (v * (1 - s * f)))
    t = int(255 * (v * (1 - s * (1 - f))))

    v *= 255

    i %= 6

    if i == 0: return v, t, p
    if i == 1: return q, v, p
    if i == 2: return p, v, t
    if i == 3: return p, q, v
    if i == 4: return t, p, v
    if i == 5: return v, p, q


def gen_rainbow(steps: int) -> Iterable[RGB]:
    for h in _nrange(0, 360, steps):
        yield hsv_to_rgb(h / 360, 1, 1)


def gen_gradient_from_rgb(start: RGB,
                          end: RGB,
                          length: int) -> Iterable[RGB]:
    """
    generate n (length) rgb values for a gradient from start to end
    """
    for i in range(length):
        yield tuple(int(start[j] + (end[j] - start[j]) * i / (length - 1)) for j in range(3))


def create_bar(length: int, *,
               progress: int = 1,
               start_color: RGB = (255, 150, 0),
               mid_color: RGB = (255, 228, 0),
               end_color: RGB = (25, 211, 0),
               arrow: tuple[str, str] = ('=', '>'),
               sides: tuple[str, str] = ('[', ']')) -> str:

    """
    generate a progress bar string with 3 blended colors
  
    args:
        length: int - total length of the bar
        progress: int - current progress

        start, mid, end color: RGB - rgb tuples for start, mid, end colors
            defaults: orange, yellow, green

        arrow: tuple[str, str] - characters to use for the arrow
            `arrow[0]` will be used for the body and `arrow[1]` for the arrowhead

        sides: tuple[str, str] - characters to use for the sides
            `sides[0]` will be used for the left side and `sides[1]` for the right side
    """

    assert len(arrow) == 2 and len(sides) == 2

    if len(arrow[0]) > 1:
        raise NotImplementedError('arrow body length > 1 is currently not supported')

    if length == 0:
        return fg.white + sides[0] + sides[1] + reset

    # only take away arrow length if it's > 1
    diff = len(sides[0] + sides[1]) + len(arrow[1]) - 1

    length -= diff
    progress -= diff

    if progress <= 0:
        return fg.white + sides[0] + ' ' * length + sides[1] + reset

    if progress > length:
        progress = length

    if not arrow[0] and not arrow[1]:
        arrow = ' ', ' '
    
    if progress == 1:
        return fg.white + sides[0] + \
               fg.rgb(*start_color) + arrow[1] + \
               ' ' * (length - 1) + \
               fg.white + sides[1] + reset

    bar_colors = chain(gen_gradient_from_rgb(start_color, mid_color, length - length // 2),
                       gen_gradient_from_rgb(mid_color, end_color, length // 2))
    
    bar = tuple(fg.rgb(*c) + arrow[0] for c in bar_colors)

    return fg.white + sides[0] + \
           ''.join(bar[:progress - 1]) + arrow[1] + \
           ' ' * len(bar[progress:]) + \
           fg.white + sides[1] + reset


def enumerate_bar(length: int, *args, **kwargs) -> tuple[int, Iterable[str]]:

    """
    create an iterable progress bar
    
    returns a tuple of the current progress and a bar iterator
    """

    if 'progress' in kwargs:
        raise ValueError('progress keyword argument will be overridden')

    for i in range(length + 1):
        yield i, create_bar(length, progress=i, *args, **kwargs)


### private methods ###

def _nrange(x: int | float,
            y: int | float,
            n: int) -> Iterable[int | float]:

    """
    generate a range of n numbers from x to y
    """

    assert n > 1, 'n must be greater than 1'
    step = (y - x) / (n - 1)
    for i in range(n):
        yield x + i * step

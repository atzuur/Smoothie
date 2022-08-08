import sys
import os
from argparse import ArgumentParser, Namespace
from types import TracebackType

import execute
from helpers import *
from plugins.colors import printp


def main(args: Namespace = None): # you can pass in your own namespace of args to use smoothie as a library

    def hook(t: BaseException, v: object, tb: TracebackType):
        printp(t(v), 'exception', extra_tb=tb) # prettyprint exceptions

    sys.excepthook = hook

    check_os()

    parser = ArgumentParser()
    add_arg = parser.add_argument

    add_arg("-peek", "-p",
            help=" Render a specific frame (outputs an image)",
            nargs=1,
            metavar="<int>",
            type=int)

    add_arg("-trim", "-t",
            help=" Trim out the parts you don't want to render, in either a timecode (hh:mm:ss) or frames (start-end)",
            nargs=1,
            metavar="<hh>:<mm>:<ss>-<hh>:<mm>:<ss> | <start>-<end>")

    add_arg("-dir",
            help=" Open the directory where Smoothie resides",
            action="store_true")

    add_arg("-recipe", "-rc",
            help=" Open the default recipe.yaml",
            action="store_true")

    add_arg("-config", "-c",
            help=" Override config file path",
            nargs=1,
            metavar="<path>")

    add_arg("-verbose", "-v",
            help=" Increase output verbosity",
            action="store_true")

    add_arg("-input", "-i",
            help=" Specify input video path(s)",
            nargs="+",
            metavar="<path>")

    add_arg("-output", "-o",
            help=" Specify output video path (only works with single inputs) or output folder."
                 " This can also be NULL (redirects to the OS's null device) or a dash (redirects to stdout)."
                 " Everything else is interpreted as a path",
            nargs=1,
            metavar="<path>")

    add_arg("-override",
            help=" Override a recipe value",
            nargs="+",
            metavar="<category>;<key>=<value>")

    if not args: args = parser.parse_args()
    script_dir = sys.path[0]

    if args.dir:
        os.startfile(script_dir)
        exit(0)

    if args.recipe:
        recipe = os.path.join(script_dir, "settings/recipe.yaml")
        if not os.path.exists(recipe):
            print(f"Default recipe (config) path does not exist: {recipe}")
            pause()
            exit(1)

        os.startfile(recipe)
        exit(0)

    if not args.input:
        parser.print_help()
        exit(1)

    for idx, file in enumerate(args.input):

        args.input[idx] = literal_path(file)

        if not os.path.isfile(file):
            raise FileNotFoundError(f"{file} does not exist")

    multi_input = len(args.input) > 1

    if args.output:
        args.output = args.output.strip()

        if args.output == "NULL":
            args.output = os.devnull

        elif args.output == "-": ... # this is just to skip the else statement below

        else:
            args.output = literal_path(args.output)

            outf = os.path.dirname(args.output) if os.path.isfile(args.output) else args.output

            if not os.path.exists(outf):
                raise FileNotFoundError(f'Output folder "{outf}" does not exist')

            if multi_input and not os.path.isdir(outf):
                raise ValueError(f'Cannot output to a file when multiple inputs are specified')

    execute.main(args)


def validate_args(args: Namespace):
    pass


if __name__ == "__main__":
    main()

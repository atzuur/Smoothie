import sys
from os import path, system, listdir
from argparse import ArgumentParser

import execute
import helpers


def main():

    helpers.checkOS()

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
            metavar="timecode=<hh>:<mm>:<ss> | frames=<start>-<end>")

    add_arg("-dir",
            help=" Opens the directory where Smoothie resides",
            action="store_true")

    add_arg("-recipe", "-rc",
            help=" Opens default recipe.yaml",
            action="store_true")

    add_arg("-config", "-c",
            help=" Override config file path",
            nargs=1,
            metavar="<PATH>")

    add_arg("-verbose", "-v",
            help=" increase output verbosity",
            action="store_true")

    add_arg("-input", "-i",
            help=" Specify input video path(s)",
            nargs="+",
            metavar="<PATH>")

    add_arg("-output", "-o",
            help=" Specify output video path (only works with single inputs) or output folder",
            nargs=1,
            metavar="<PATH>")

    add_arg("-override",
            help=" Override a recipe value",
            nargs="+",
            metavar="<category>;<key>=<value>")

    args = parser.parse_args()
    script_dir = sys.path[0]

    if args.dir:

        if helpers.isWin:
            system(f'explorer {script_dir}')
        else:
            print("")
            system(f'xdg-open {script_dir}')

        exit(0)

    if args.recipe:

        recipe = path.join(script_dir, "settings/recipe.yaml")

        if not path.exists(recipe):
            print(f"Default recipe (config) path does not exist: {recipe}")
            helpers.pause()
            exit(1)

        if helpers.isWin:
            system(recipe)
        else:
            system(f'xdg-open {recipe}')

        exit(0)

    if not args.input:
        parser.print_help()
        exit(1)

    for idx, file in enumerate(args.input):

        if helpers.isLinux:
            args.input[idx] = path.expanduser(args.input[idx])

        args.input[idx] = path.abspath(file)

        if not path.isfile(file):
            raise FileNotFoundError(f"{file} does not exist")

    multi_input = len(args.input) > 1

    if args.output:

        if helpers.isLinux:
            args.output = path.expanduser(args.output)

        args.output = path.abspath(args.output)

        outf = path.dirname(args.output)
        output_to_folder: bool = outf == args.output # if output is the same as it's dirname, then it's a folder

        if not path.exists(outf):
            raise FileNotFoundError(f"{outf} does not exist")

        if multi_input and not output_to_folder:
            args.output = outf

        if path.isfile(args.output):
            if input(f"{args.output} already exists, overwrite? [y/n]").casefold().strip() not in helpers.yes:
                exit(1)
    else:
        args.output = None

    execute.main(args)

if __name__ == "__main__":
    main()

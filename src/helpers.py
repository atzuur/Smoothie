from getpass import getpass
from json import loads
from sys import exit
from subprocess import run, PIPE
from re import search
from platform import architecture, system as ossystem
from os import environ
from glob import glob

global isWT
isWT = environ.get('WT_PROFILE_ID') != None # This environemnt variable spawns with WT

def probe(file_path:str):
    
    command_array = ["ffprobe",
                 "-v", "quiet",
                 "-print_format", "json",
                 "-show_format",
                 "-show_streams",
                 file_path]
    result = run(command_array, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    return [
        result.returncode,
        loads(result.stdout),
        result.stderr]
    
def fps(file_path:str):
    r_frame_rate = probe(file_path)[1]['streams'][0]['r_frame_rate']
    return round(eval(r_frame_rate))
    
def setWTprogress(value:int,color:str=None): # Modified from https://github.com/oxygen-dioxide/wtprogress
    if(color!=None):
        color={"green":1,"g":1,"red":2,"r":2,"yellow":4,"y":4}[color]
    else:
        color="1"
    value=int(value)
    print("\x1b]9;4;{};{}\x1b\\".format(color,value),end="",flush=True)
    
def checkOS():
    if architecture()[0] != '64bit':
        print('Smoothie is only compatible with 64bit systems.')
        exit(1)

    if ossystem() not in ['Linux', 'Windows']:
        # If hasn't returned yet then throw
        print(f'Unsupported OS "{ossystem()}"')
        exit(1)

global isLinux, isWin
isLinux = ossystem() == 'Linux'
isWin = ossystem() == 'Windows'

def pause():
    getpass('Press enter to continue..')


def literal_path(path: str):
    


# Bool aliases
yes = ['True','true','yes','y','1', True]
no = ['False','false','no','n','0','null','',None, False]


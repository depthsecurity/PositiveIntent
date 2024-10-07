import argparse
import math

def shannon_entropy(data):
    # 256 different possible values
    possible = dict(((chr(x), 0) for x in range(0, 256)))

    for byte in data:
        possible[chr(byte)] +=1

    data_len = len(data)
    entropy = 0.0

    # compute
    for i in possible:
        if possible[i] == 0:
            continue

        p = float(possible[i] / data_len)
        entropy -= p * math.log(p, 2)
    return entropy

def run():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..\\temp\\PositiveIntent\\bin\\Release\\net48\\PositiveIntent.exe"), 'rb') as file:
        return(shannon_entropy(file.read()))
        

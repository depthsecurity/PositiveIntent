import argparse
import math
import os

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
    return round(entropy, 2)

def run(assembly_output_path):
    with open(assembly_output_path, 'rb') as file:
        return(shannon_entropy(file.read()))
        

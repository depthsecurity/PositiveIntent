import os
import colorama
import sys
import argparse

class RC4:
    def __init__(self, key):
        self.S = list(range(256))  # Initialize the state array S
        self.x = 0
        self.y = 0
        self.key_setup(key)

    def key_setup(self, key):
        key_length = len(key)
        j = 0
        for i in range(256):
            j = (j + self.S[i] + key[i % key_length]) % 256
            self.swap(i, j)

    def swap(self, i, j):
        self.S[i], self.S[j] = self.S[j], self.S[i]

    def encrypt_decrypt(self, data):
        output = bytearray(len(data))
        for k in range(len(data)):
            self.x = (self.x + 1) % 256
            self.y = (self.y + self.S[self.x]) % 256
            self.swap(self.x, self.y)
            key_stream = self.S[(self.S[self.x] + self.S[self.y]) % 256]
            output[k] = data[k] ^ key_stream
        return output

if __name__=="__main__":

    if sys.platform == 'win32':
        colorama.init()

    parser = argparse.ArgumentParser(description='PositiveIntent .NET Loader')
    parser.add_argument('--file', type=argparse.FileType('rb'),
                        required=True, help='Path to your encrypted output file.')
    parser.add_argument('--key', type=str,
                        required=True, help='Your decryption key (check build output).')
    args = parser.parse_args()

    file_bytes = args.file.read()
    rc4 = RC4(args.key.encode('utf-8'))
    print(rc4.encrypt_decrypt(file_bytes).decode('utf-8'))

"""
GOST 28147-89 cipher that includes 4 modes:
    ECB - Electronic Codebook - Режим простой замены
    CNT - Counter - Режим гаммирования
    CFB - Cipher Feedback - Режим гаммирования с обратной связью
    MAC - Message Authentication Code - Режим выработки имитовставки
There are two modes:
    mode = 1 - decryption
    mode = 0 - encryption
"""

import random
import math
import sys
import argparse
import textwrap

class GOST_28147():

    def __init__(self, key, synchro):
        self.key = key
        self.synchro = synchro
        self.set_key()
        self.set_s_box()
        self.C1 = 0x1010104
        self.C2 = 0x1010101
    
    def set_key(self):
        # Key generation
        if self.key == None:
            k = []
            for _ in range(8):
                tmp = random.getrandbits(32)
                k.append(tmp)
            self.subkeys = k
        # Setting the input key
        else:
            tmp = (4 - self.key.bit_length() % 4) % 4
            tmp_key = int(('0b1' + '0' * (self.key.bit_length() + tmp)), 2) | self.key
            tmp_key = str(bin(tmp_key))[3:]
            self.subkeys = []
            for _ in range(8):
                self.subkeys.append(int(('0b' + tmp_key[:32]), 2))
                tmp_key = tmp_key[32:]
            #self.subkeys = [(self.key >> (32 * i)) & 0xFFFFFFFF for i in range(8)]

    def set_s_box(self):
        self.s_box = [
            [4, 10, 9, 2, 13, 8, 0, 14, 6, 11, 1, 12, 7, 15, 5, 3],
            [14, 11, 4, 12, 6, 13, 15, 10, 2, 3, 8, 1, 0, 7, 5, 9],
            [5, 8, 1, 13, 10, 3, 4, 2, 14, 15, 12, 7, 6, 0, 9, 11],
            [7, 13, 10, 1, 0, 8, 9, 15, 14, 4, 6, 12, 11, 2, 5, 3],
            [6, 12, 7, 1, 5, 15, 13, 8, 4, 10, 9, 14, 0, 3, 11, 2],
            [4, 11, 10, 0, 7, 2, 1, 13, 3, 6, 8, 5, 9, 12, 15, 14],
            [13, 11, 4, 1, 3, 15, 5, 9, 0, 10, 14, 7, 6, 8, 2, 12],
            [1, 15, 13, 0, 5, 7, 10, 4, 9, 2, 3, 14, 6, 11, 8, 12]
        ]
    
    # Division into two parts
    def left_right(self, data):
        n2 = data >> 32
        n1 = data & 0xFFFFFFFF
        
        return (n1, n2)

    def replacement_table(self, s):
        ans = 0
        for i in range(8):
            # Getting 4 bits from the end using shifts
            tmp = s >> 4*i & 0xF
            ans += self.s_box[i][tmp] << 4*i
        
        return ans

    def main_step(self, data, sub_key):
        n1, n2 = self.left_right(data)
        S = (n1 + sub_key) % 4294967296
        S = self.replacement_table(S)
        S = (S << 11) & 0xFFFFFFFF | S >> 21
        S = S ^ n2
        n2 = n1
        n1 = S
       
        return n2 << 32 | n1

    def cycle_32_Z(self, data):
        for _ in range(3):
            for j in range(8):
                data = self.main_step(data, self.subkeys[j])
        for j in range(7, -1, -1):
            data = self.main_step(data, self.subkeys[j])
        n2, n1 = self.left_right(data)
        return n2 << 32 | n1
    
    def cycle_32_R(self, data):
        for j in range(8):
            data = self.main_step(data, self.subkeys[j])
        for _ in range(3):
            for j in range(7, -1, -1):
                data = self.main_step(data, self.subkeys[j])
        n2, n1 = self.left_right(data)
        
        return n2 << 32 | n1

    def cycle_16_Z(self, data):
        for _ in range(2):
            for j in range(8):
                data = self.main_step(data, self.subkeys[j])
        
        return data
    
    # Dividing the input text into 64-bit blocks
    def make_block(self, data):
        tmp = (4 - data.bit_length() % 4) % 4
        data = int(('0b1' + '0' * (data.bit_length() + tmp)), 2) | data
        ans = []
        tmp_data = str(bin(data))[3:]
        cnt_blocks = math.ceil(len(tmp_data) / 64)
        for _ in range(cnt_blocks-1):
            block = '0b' + tmp_data[:64]
            tmp_data = tmp_data[64:]
            ans.append(int(block, 2))
        block = '0b' + tmp_data
        ans.append(int(block, 2))
        
        return ans
    
    def ECB(self, data, mode=0):
        # Getting leading zeros for a full hexadecimal value
        tmp = (4 - data.bit_length() % 4) % 4
        tmp_data = int(('0b1' + '0' * (data.bit_length() + tmp)), 2) | data
        tmp_data = str(bin(tmp_data))[3:]
        # Checking file size divisibility by 64
        if len(tmp_data) % 64 != 0:
            print("Length of data is:", len(tmp_data))
            print("Error!!! Not divisible by 64!")
            raise ZeroDivisionError
        plain_text = self.make_block(data)
        ans = 0
        for i in range(len(plain_text)):
            if mode:
                crypt_text = self.cycle_32_Z(plain_text[i])
            else:
                crypt_text = self.cycle_32_R(plain_text[i])
            ans = ans << 64 | crypt_text    
        return ans, int('0x' + ''.join([hex(x)[2:] for x in self.subkeys]), 16)
        
    def CNT(self, data, mode=0):
        # Initialization vector generation
        if not mode:
            if self.synchro == None:
                self.synchro = random.getrandbits(64)
        self.synchro = self.synchro & 0xFFFFFFFFFFFFFFFF
        
        gamma = self.cycle_32_Z(self.synchro)
        plain_text = self.make_block(data)
        ans = 0

        for i in range(len(plain_text)-1):
            n3, n4 = self.left_right(gamma)
            n3 = (n3 + self.C2) % 4294967296
            if n4 + self.C1 >= 4294967296:
                n4 = n4 + self.C1 - 4294967296 + 1
            else:
                n4 = n4 + self.C1
            gamma = n4 << 32 | n3
            crypt_text = gamma ^ plain_text[i]
            ans = ans << 64 | crypt_text 
        
        # Getting leading zeros for a full hexadecimal value
        tmp = (4 - plain_text[-1].bit_length() % 4) % 4 + plain_text[-1].bit_length()
        gamma = int(str(bin(gamma))[:tmp], 2)
        crypt_text = gamma ^ plain_text[-1]
        ans = ans << tmp | crypt_text

        if mode == 0:
            return ans, self.synchro, int('0x' + ''.join([hex(x)[2:] for x in self.subkeys]), 16)
        else:
            return ans

    def CFB(self, data, mode=0):
        if not mode:
            if self.synchro == None:
                self.synchro = random.getrandbits(64)
            else:
                self.synchro = self.synchro & 0xFFFFFFFFFFFFFFFF
        gamma = self.synchro
        
        plain_text = self.make_block(data)
        ans = 0

        for i in range(len(plain_text)):
            gamma = self.cycle_32_Z(gamma)
            crypt_text = plain_text[i] ^  gamma
            ans = ans << 64 | crypt_text
            if mode:
                gamma = plain_text[i]
            else:
                gamma = crypt_text
        
        if mode == 0:
            return ans, self.synchro, int('0x' + ''.join([hex(x)[2:] for x in self.subkeys]), 16)
        else:
            return ans

    def MAC(self, data, mac_length):
        s = 0
        plain_text = self.make_block(data)
        # Padding with zeros up to a 64 bit block
        if plain_text[-1].bit_length() != 64:
            plain_text[-1] = plain_text[-1] << (64 - plain_text[-1].bit_length())
        for i in plain_text:
            s = self.cycle_16_Z(s ^ i)
        
        return s & (2 ** mac_length - 1)      

def create_parser():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--chk', action='store_const', const=True,
            help="Осуществление шифрования и расшифрования по входным данным")
    parser.add_argument('-m', '--mode', choices=['0', '1'], default='0', 
            help="Выбор режима шифрования:\n\t0 - для шифрования\n\t1 - для расшифрования",
            metavar='MODE')
    parser.add_argument('--algo', choices=['ECB', 'CNT', 'CFB'], required=True,
            help="""Выбор алгоритма шифрования:
        ECB - Режим простой замены
        CNT - Режим гаммирования
        CFB - Режим гаммирования с обратной связью""")
    parser.add_argument('--MAC', action='store_const', const=32,
            help="Выбор режима выработки имитовставки")
    parser.add_argument('-r', '--read', type=argparse.FileType(), required=True,
            help="Путь к файлу с входными данными",
            metavar='FILE')
    parser.add_argument('-w', '--write', type=argparse.FileType(mode='w'),
            help="Путь к файлу с выходными данными\nПо умолчанию вывод результатов осуществляется в командную строку",
            metavar='FILE')
    parser.add_argument('--key', action='store_const', const=True,
            help="Ввод ключа вручную с командной строки.\nПо умолчанию ключ генерируется системой")
    parser.add_argument('--syn', action='store_const', const=True,
            help="Ввод синхропосылки вручную с командной строки.\nПо умолчанию генерируется системой") 

    return parser

def input_processing():
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])   
    mode = 1 if namespace.mode == '1' else 0
    # Getting the key
    if namespace.key != None or mode:
        print("Please enter the key in hexadecimal format (like 0x...):")
        key = input()
        if len(key) != 66:
            print("Key must be 256 bit. It will be generated by system!")
            key = None
        else:
            key = int(key, 16)
    else:
        key = None
    # Getting the initialization vector
    if namespace.syn != None or (mode and (
        namespace.algo == 'CNT' or namespace.algo == 'CFB')):
        print("Please enter the initialization vector in hexadecimal format (like 0x...):")
        syn = int(input(), 16)
    else:
        syn = None
    # Initializating the class
    try:    
        gost = GOST_28147(key, syn)
    except ValueError:
        print("Key and/or initialization vector must be in hexadecimal format (like 0x...)")
        sys.exit()
    try:
        text = namespace.read.read()
        # exclude MAC from text data
        if mode == 1 and namespace.MAC != None:
            mac_length = 8
            check_MAC = int(('0x' + text[-mac_length:]), 16)  
            text = text[:-mac_length]     
        if mode == 0:
            text = int('0x' + text.encode().hex(), 16)
        else:
            text = int(text, 16)
    finally:
        namespace.read.close()

    # Choosing algorithm
    if namespace.algo == 'ECB':
        if namespace.chk != None:
            print("Mode = ECB")
            print("Plain data is:", bytes.fromhex(hex(text)[2:]).decode())
            ans = gost.ECB(text, mode=0)
            print("Crypt text is:", hex(ans))
            ans = gost.ECB(ans, mode=1)
            print("Decoded text is:", bytes.fromhex(hex(ans)[2:]).decode())
        else:
            ans, key = gost.ECB(text, mode)
            print("Key is:\n", hex(key))
    if namespace.algo == 'CFB':
        # Check mode of CFB
        if namespace.chk != None:
            print("Mode = CFB")
            print("Plain data is:", bytes.fromhex(hex(text)[2:]).decode())
            ans, _, _ = gost.CFB(text, mode=0)
            print("Crypt text is:", hex(ans))
            ans = gost.CFB(ans, mode=1)
            print("Decoded text is:", bytes.fromhex(hex(ans)[2:]).decode())
        else:
            if mode == 0:
                ans, syn, key = gost.CFB(text, mode=mode)
                print("Key is:\n", hex(key))
                print("Initialization vector is:\n", hex(syn))
            else:
                ans = gost.CFB(text, mode=mode)      
    if namespace.algo == 'CNT':
        # Check mode of CNT
        if namespace.chk != None:
            print("Mode = CNT")
            ans, _, _ = gost.CNT(text, mode=0)
            ans = gost.CNT(ans, mode=1)
            print("Decoded text is:", bytes.fromhex(hex(ans)[2:]).decode())
        else:
            if mode == 0:
                ans, syn, key = gost.CNT(text, mode=mode)
                print("Initialization vector is:\n", hex(syn))
                print("Key is:\n", hex(key))
            else:
                ans = gost.CNT(text, mode=mode)
    # Checking MAC
    if namespace.MAC != None:
        if mode:
            get_MAC = gost.MAC(ans, namespace.MAC)
            print("Real MAC is:",hex(get_MAC))
            print("Counted MAC is:", hex(check_MAC)) 
            if check_MAC != get_MAC:
                print("Don't match MAC! The data has probably been changed!")
            else:
                print("MAC checking has been done! There is no error!")
        else:
            get_MAC = gost.MAC(text, namespace.MAC)
            print("MAC is:", hex(get_MAC))
            ans = ans << namespace.MAC | get_MAC
    if mode:
        ans = bytes.fromhex(hex(ans)[2:]).decode()
    if namespace.chk == None:       
        if namespace.write != None:
            if mode:
                namespace.write.write(ans)
            else:
                namespace.write.write(hex(ans))
            namespace.write.close()
        else:
            print("\nResult is:")
            print(hex(ans))

if __name__ == "__main__":
    random.seed()
    try:
        input_processing()
    except ZeroDivisionError:
        print('Try again!')
    except Exception as e:
        print("Something went wrong:", e)


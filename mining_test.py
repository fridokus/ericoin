import hashlib
import time
import math
import random


def number_to_bytes(number):
    nibble_count = int(math.log(number, 256)) + 1
    hex_string = '{:0{}x}'.format(number, nibble_count * 2)
    return bytearray.fromhex(hex_string)


def find_block(target_int):
    nonce = random.randint(0, 1e63)
    block_found = 0
    while not block_found:
        nonce += 1
        bytes_input = number_to_bytes(nonce)
        guess = hashlib.sha256(bytes_input).hexdigest()
        guess_int = int(guess, 16)
        if guess_int < target_int:
            block_found = 1
    return nonce, guess

def print_target(target_int):
    str_hex_target = str(hex(target_int))
    target_str = '0x' + ''.join(['0' for i in range(64 - len(str_hex_target) + 2)]) + str_hex_target[2:]
    print('| --- Target: %s ---\n|' % target_str)


def main():
    target = '0000' + ''.join(['f' for i in range(64 - 4)])
    block_time = 4
    blocks_per_adjust = 10
    time_l = []
    nonce_l = []
    target_int = int(target, 16)
    print('| Block time: %.2f seconds. Blocks per difficulty adjustment: %d' % (block_time, blocks_per_adjust))
    print_target(target_int)
    while 1:
        for i in range(blocks_per_adjust):
            now = time.time()
            nonce, guess = find_block(target_int)
            time_taken = time.time() - now
            nonce_l.append(nonce)
            time_l.append(time_taken)
            print('⎅ Block with hash %s found in %.2f seconds.' % (str(guess), time_taken))
        sum_time = sum(time_l[-(blocks_per_adjust):])
        adjustment_factor = sum_time / blocks_per_adjust / block_time
        target_int = int(target_int * adjustment_factor)
        print('|\n| --- Time taken for %d blocks: %.2f seconds. Adjusting difficulty by factor %.4f. ---' \
                % (blocks_per_adjust, sum_time, 1/adjustment_factor))
        print_target(target_int)
        


if __name__ == '__main__':
    main()

#!/usr/bin/env python3

import os

NUMBER_OF_TICKS = 11
CIPHER_NAME = 'strumok512'
MAX_GUESSES = 7
MAX_STEPS = 15

def build_relation_file(number_of_ticks=NUMBER_OF_TICKS):
    file_lines = []
    file_lines.append(f'#{CIPHER_NAME} {number_of_ticks} Rounds')
    file_lines.append('connection relations')

    for tick in range(number_of_ticks):
        lfsr_word_at_tick = f'w_{tick}'
        lfsr_word_11_ahead = f'w_{tick + 11}'
        lfsr_word_13_ahead = f'w_{tick + 13}'
        lfsr_word_15_ahead = f'w_{tick + 15}'
        lfsr_new_feedback_word = f'w_{tick + 16}'

        r1_this_tick = f'R1_{tick}'
        r2_this_tick = f'R2_{tick}'
        r1_next_tick = f'R1_{tick + 1}'
        r2_next_tick = f'R2_{tick + 1}'

        file_lines.append(
            f'{lfsr_new_feedback_word}, {lfsr_word_11_ahead}, '
            f'{lfsr_word_at_tick}, {lfsr_word_13_ahead}'
        )

        file_lines.append(
            f'{r2_next_tick}, {r1_this_tick}'
        )

        file_lines.append(
            f'{r1_next_tick}, {r2_this_tick}, {lfsr_word_13_ahead}'
        )

        file_lines.append(
            f'{lfsr_word_15_ahead}, {r1_this_tick}, '
            f'{r2_this_tick}, {lfsr_word_at_tick}'
        )

    file_lines.append('known')
    for tick in range(number_of_ticks):
        file_lines.append(f'z_{tick}')

    file_lines.append('target')
    for tick in range(16):
        file_lines.append(f'w_{tick}')
    file_lines.append('R1_0')
    file_lines.append('R2_0')

    file_lines.append('end')

    output_filename = (
        f'relations1.txt'
    )
    output_path = os.path.join(os.path.dirname(__file__), output_filename)

    with open(output_path, 'w') as output_file:
        output_file.write('\n'.join(file_lines))

    all_equations = [
        line for line in file_lines
        if line and not line.startswith('#') and line not in ('connection relations', 'end')
    ]
    all_variable_names = set()
    for equation_line in all_equations:
        for variable_name in equation_line.split(','):
            all_variable_names.add(variable_name.strip())

    print(f'File saved:  {output_path}')
    print(f'Total variables:  {len(all_variable_names)}')
    print(f'Total equations:  {len(all_equations)}')
    print()
    print(f'Command for Autoguess:')
    print(f'  python3 autoguess.py -i {output_filename} -s sat -mg {MAX_GUESSES} -ms {MAX_STEPS}')
    return output_path

if __name__ == '__main__':
    build_relation_file()
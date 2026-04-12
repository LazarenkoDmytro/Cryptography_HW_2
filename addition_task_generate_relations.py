#!/usr/bin/env python3

import os

NUMBER_OF_TICKS = 12
CIPHER_NAME = 'strumok512'
MAX_GUESSES = 6
MAX_STEPS = 20


def build_relation_file(number_of_ticks=NUMBER_OF_TICKS):
    file_lines = []
    file_lines.append(f'#{CIPHER_NAME} {number_of_ticks} Rounds')
    file_lines.append('connection relations')

    for tick in range(number_of_ticks):
        w_t = f'w_{tick}'
        w_11 = f'w_{tick + 11}'
        w_13 = f'w_{tick + 13}'
        w_15 = f'w_{tick + 15}'
        w_new = f'w_{tick + 16}'

        R1_t = f'R1_{tick}'
        R2_t = f'R2_{tick}'
        R1_next = f'R1_{tick + 1}'
        R2_next = f'R2_{tick + 1}'

        z = f'z_{tick}'
        file_lines.append(
            f'{w_new}, {w_11}, {w_t}, {w_13}'
        )

        file_lines.append(
            f'{w_t}, {w_new}, {w_11}, {w_13}'
        )

        file_lines.append(
            f'{R2_next}, {R1_t}'
        )

        file_lines.append(
            f'{R1_next}, {R2_t}, {w_13}'
        )

        file_lines.append(
            f'{z}, {w_15}, {R1_t}, {R2_t}, {w_t}'
        )

    file_lines.append('known')
    for tick in range(number_of_ticks):
        file_lines.append(f'z_{tick}')
    file_lines.append('target')

    for i in range(4):
        file_lines.append(f'w_{i}')

    file_lines.append('R1_0')
    file_lines.append('R2_0')
    file_lines.append('end')
    output_filename = f'relations_addition_task.txt'
    output_path = os.path.join(os.path.dirname(__file__), output_filename)

    with open(output_path, 'w') as f:
        f.write('\n'.join(file_lines))

    all_equations = [
        line for line in file_lines
        if line and not line.startswith('#')
        and line not in ('connection relations', 'known', 'target', 'end')
    ]

    variables = set()
    for eq in all_equations:
        for v in eq.split(','):
            variables.add(v.strip())

    print(f'File saved: {output_path}')
    print(f'Variables: {len(variables)}')
    print(f'Equations: {len(all_equations)}')
    print("The command to run:")
    print(f'  python3 autoguess.py -i {output_filename} -s sat -mg {MAX_GUESSES} -ms {MAX_STEPS}')
    return output_path

if __name__ == '__main__':
    build_relation_file()
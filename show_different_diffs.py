"""show_different_diffs.py

In the react source code, most files are duplicated-- for example,
ReactFiberBeginWork.new.js is exactly the same as
ReactFiberBeginWork.old.js, the only difference being the imports at the
top of the file.

The goal of this script is to find out which duplicated files in the
react codebase have non-trivial differences between them.

Usage: python show_different_diffs.py /react-source-dir
"""

import sys
import os
import os.path
import re
from typing import Callable


DIFF_COMMAND = '/usr/bin/diff'

Command = str # Type: The command used to invoke the diff program


def run_command(command: Command) -> str:
    """Run the command and return its output"""
    return os.popen(command).read()

# Checks a line of diff output, if the line doesn't match, a non-trivial difference was found
TRIVIAL_PATTERN = re.compile(r"""
    \d+(?:,\d+)?c\d+(?:,\d+)?  | # Line number info
    (?:<|>).*(?:new|old)';     | # import\export line
    ---                          # Separator
""", re.VERBOSE)

def is_non_trivial(diff_output: str) -> bool:
    """Examine the diff output and determine whether the .old and .new
    files have non trivial differences-- i.e. differences other than
    import filenames
    """
    return any(TRIVIAL_PATTERN.match(line) is None
               for line in diff_output.splitlines())


FILENAME_PATTERN = re.compile(r'(?P<filename_start>.*?)\.new\.js$')

def enqueue_work(enqueue: Callable[[Command], None], react_dir: str):
    packages = os.path.join(react_dir, 'packages')
    if not os.path.isdir(packages):
        raise RuntimeError('Invalid React source directory')

    for dirpath, _, filenames in os.walk(packages):
        filename_set = set()
        for filename in filenames:
            filename_set.add(os.path.join(dirpath, filename))
        for filename in filename_set:
            if (match := FILENAME_PATTERN.match(filename)):
                old_filename = match.group('filename_start') + '.old.js'
                if old_filename in filename_set:
                    command = f'{DIFF_COMMAND} {filename} {old_filename}'
                    enqueue(command)


def main(*, react_dir: str):
    work = []
    enqueue_work(work.append, react_dir)

    results = []
    for command in work:
        diff_output = run_command(command)
        if is_non_trivial(diff_output):
            results.append(command)

    if results:
        for result in results:
            print(result)
    else:
        print("No non-trivial differences found!")

if __name__ == '__main__':
    main(react_dir=sys.argv[1])

# Result: There are no non-trivial differences
# 2022-01-26

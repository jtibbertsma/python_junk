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
from queue import Queue, Empty
from dataclasses import dataclass
from threading import Thread
from typing import Callable

DIFF_COMMAND = '/usr/bin/diff'
NUM_WORKER_THREADS = 8

Command = str # Type: The command used to invoke the diff program
Result = Command | tuple[Exception, Command]


def run_command(command: Command) -> str:
    """Run the command and return its output"""
    return os.popen(command).read()

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

@dataclass
class Worker:
    """Thread target"""
    work: Queue[Command]
    results: list[Result]

    def __call__(self, checkfinished: Callable[[], bool]):
        work = self.work
        results = self.results

        while True:
            try:
                command = work.get(timeout=0.1)
            except Empty:
                if checkfinished():
                    break
                continue
            try:
                diff_output = run_command(command)
                if is_non_trivial(diff_output):
                    results.append(command)
            except Exception as e:
                results.append((e, command))
            finally:
                work.task_done()

class Threadpool:
    def __init__(self, *, target: Worker):
        self.threadlist: list[Thread] = []
        self.killed = None

        for _ in range(NUM_WORKER_THREADS):
            thread = Thread(target=target, args=(self.isdead,))
            self.threadlist.append(thread)

    def start(self):
        self.killed = False
        for thread in self.threadlist:
            thread.start()

    def kill(self):
        """End the execution of worker threads and wait for them to finish"""
        if self.killed is False:
            self.killed = True
            for thread in self.threadlist:
                thread.join()

    def isdead(self):
        return self.killed is True


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
    # Initialize queue

    # Initialize threadpool

    # Main thread:
    #   Find same files and enqueue

    # Worker threads:
    #   Wait for output of diff and check for non-trivial differences

    work = Queue()
    results: list[Result] = []

    threadpool = Threadpool(target=Worker(work, results))
    threadpool.start()

    enqueue_work(work.put, react_dir)

    work.join()
    threadpool.kill()

    for result in results:
        print(result)

if __name__ == '__main__':
    main(react_dir=sys.argv[1])

# Result: There are no non-trivial differences
# 2022-01-26

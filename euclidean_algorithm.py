"""
Program that takes two integers and uses the Euclidean Algorithm to find the GCD
"""
import sys
from typing import List

__all__ = [
  'simple_euclidean_algorithm',
  'least_common_multiple',
  'print_euclidean_algorithm_table',
  'AlgorithmStep',
  'generate_algorithm_steps',
  'print_steps'
]

DEFAULT_PADDING = 7
TITLE_ROW = ['Quotient', 'Remainder', 'X_0', 'Y_0']

def simple_euclidean_algorithm(a: int, b: int) -> int:
  """
  Use the Euclidean Algorithm to find the GCD g = (a, b) of integers a and b without
  recording the intermediate steps of the algorithm
  """
  assert a > 0 and b > 0
  if a < b:
    a, b = b, a
  while b > 0:
    a, b = b, a % b
  return a

def least_common_multiple(a: int, b: int) -> int:
  """
  Find the LCM [a, b] of integers a and b, using the formula (a,b) * [a,b] = |ab|
  """
  assert a > 0 and b > 0
  ab = a * b
  gcd = simple_euclidean_algorithm(a, b)
  return ab // gcd

def print_euclidean_algorithm_table(a: int, b: int, padding=DEFAULT_PADDING) -> None:
  """
  Use the Euclidean Algorithm to find the GCD g = (a, b) of integers a and b, along with
  coefficients x and y such that g = ax + by

  Prints out each step of the algorithm in tabular form. The optional argument 'padding' is
  the amount of space between each column.
  """
  assert a > 0 and b > 0
  if b > a:
    a, b = b, a
  steps = generate_algorithm_steps(a, b)
  print_steps(steps, padding)

class AlgorithmStep(object):
  """
  Each AlgorithmStep represents one row of the algorithm table printed by the main program
  """
  __slots__ = ['quotient', 'remainder', 'x', 'y']

  def __init__(self, quotient, remainder, x, y):
    self.quotient = quotient
    self.remainder = remainder
    self.x = x
    self.y = y

  def __repr__(self):
    return str((self.quotient, self.remainder, self.x, self.y))

  @classmethod
  def generate_next(cls, steps):
    """
    Given a list of steps, generate the next step in the Euclidean Algorithm. Each step is
    computed from the previous two steps.

    Return None if the algorithm is finished.
    """
    assert len(steps) >= 2

    s_2 = steps[-2]
    s_1 = steps[-1]

    a = s_2.remainder
    b = s_1.remainder
    quotient = s_1.quotient
    remainder = a - quotient*b

    # If remainder is 0, then we were done in the previous step
    if remainder == 0:
      return None

    # Compute coefficients for this step
    x = s_2.x - quotient*s_1.x
    y = s_2.y - quotient*s_1.y

    next_quotient = b // remainder
    return cls(next_quotient, remainder, x, y)

def generate_algorithm_steps(a: int, b: int) -> List[AlgorithmStep]:
  assert a > 0 and b > 0
  if b > a:
    a, b = b, a

  # The first two "steps" represent the first two rows of the table with the first quotient
  steps = [
    AlgorithmStep(None, a, 1, 0),
    AlgorithmStep(a // b, b, 0, 1)
  ]

  while True:
    next_step = AlgorithmStep.generate_next(steps)
    # If generate_next returned None, we're done
    if next_step is None:
      break
    steps.append(next_step)
  return steps

def print_steps(steps: List[AlgorithmStep], padding: int) -> None:
  """
  Print the algorithm table and the GCD equation
  """
  max_title_length = max(map(len, TITLE_ROW))

  def find_width(get_item):
    max_length = max(map(lambda x: len(str(get_item(x))), steps))
    max_length = max(max_length, max_title_length)
    return max_length + padding

  col1_width = find_width(lambda x: x.quotient if x is not None else 0)
  col2_width = find_width(lambda x: x.remainder)
  col3_width = find_width(lambda x: x.x)
  col4_width = find_width(lambda x: x.y)

  def print_step(quotient, remainder, x, y):
    print('{:>{col1_width}}{:>{col2_width}}{:>{col3_width}}{:>{col4_width}}'.format(
      str(quotient) if quotient is not None else '',
      str(remainder),
      str(x),
      str(y),
      col1_width=col1_width,
      col2_width=col2_width,
      col3_width=col3_width,
      col4_width=col4_width
    ))

  def print_gcd_equation():
    a = steps[0].remainder
    b = steps[1].remainder
    x = steps[-1].x
    y = steps[-1].y
    gcd = steps[-1].remainder
    space = ' ' * (padding + 1)
    sign = '-'

    if x < 0:
      x *= -1
      a, b = b, a
      x, y = y, x
    elif y < 0:
      y *= -1
    else:
      sign = '+'

    print('{space}GCD = {gcd} = {x}({a}) {sign} {y}({b})'.format(
      space=space,
      gcd=gcd,
      sign=sign,
      a=a,
      b=b,
      x=x,
      y=y
    ))

  print_step(*TITLE_ROW)
  for step in steps:
    print_step(step.quotient, step.remainder, step.x, step.y)

  print()
  print_gcd_equation()

if __name__ == '__main__':
  def error_out(msg):
    print('Error: {}'.format(msg), file=sys.stderr)
    exit(1)

  def main():
    try:
      a = int(sys.argv[1])
      b = int(sys.argv[2])
      if a < 1 or b < 1:
        error_out('a and b must be greater than or equal to 1')
      print_euclidean_algorithm_table(a, b)
    except IndexError:
      error_out('not enough argument given: need 2 integers')
    except ValueError:
      error_out('arguments must be integers')
    exit(0)

  main()

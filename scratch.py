'''Scratch paper for leetcode'''
from typing import List, Tuple
import re

def get_subdomains(toplevel_domain: str) -> List[str]:
    '''Get subdomains from toplevel domain

    Ex:
    "discuss.leetcode.com" -> [
        "discuss.leetcode.com",
        "leetcode.com",
        "com"
    ]
    '''
    domains = [toplevel_domain]
    for i, c in enumerate(toplevel_domain):
        if c == '.':
            domains.append(toplevel_domain[i+1:])
    return domains

def parse_cpdomain(cpdomain: str) -> Tuple[int, List[str]]:
    match = re.match('(\d+)\s+([\w.]+)', cpdomain)
    return int(match[1]), get_subdomains(match[2])

# def has_group_of_size_m(data: int, m: int):


if __name__ == '__main__':
    print(get_subdomains("discuss.leetcode.com"))
    print(parse_cpdomain("9001 discuss.leetcode.com"))
    # [1,2,3,4]

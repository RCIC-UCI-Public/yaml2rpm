#!/bin/env python
# Generate an ansible file from a manifest 

import argparse
import sys
#    from __future__ import print_function

if sys.version_info.major == 3:
    from typing import Dict

TEMPLATE = """---
- name: %s admix packages
  yum:
    name: "{{ pkglist }}"
    state: latest
  vars:
    pkglist:"""
PKGSTR = "      - %s"

## *****************************
## main routine
## *****************************

def main(argv):

    admixName = "UNKNOWN"
    # description and help lines for the usage  help
    description = "reads a list of package names from the command line and \n" 
    description += "creates an ansible playbook with these listed\n"

    helpname = "Name of the admix that created this list. Defaults to UNKNOWN\n"

    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-n", "--name", dest="admixName", default=admixName, help=helpname)
    # required positional argument
    parser.add_argument("pkgs",  action="store", help="packages to be installed", nargs='+') 
    args = parser.parse_args()
    
    print(TEMPLATE % args.admixName)
    for pkg in args.pkgs:
        print(PKGSTR % pkg)

if __name__ == "__main__":
    main(sys.argv[1:])
        

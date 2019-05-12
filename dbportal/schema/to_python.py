"Produce raw Python code from JSON."

import json
import os.path
import pprint
import sys

infilename = sys.argv[1]
name = os.path.splitext(os.path.basename(infilename))[0]

with open(infilename) as infile:
    data = json.load(infile)

outfilename = name + '_raw.py'
with open(outfilename, 'w') as outfile:
    outfile.write('schema = ')
    outfile.write(pprint.pformat(data))

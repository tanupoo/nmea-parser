#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import argparse
from datetime import datetime
import json
from nmea_parser import nmea_parser

pa = argparse.ArgumentParser(description="put a condition of GNSS.")
pa.add_argument("-B", action="store_true", dest="break_mode",
               help="enables to show a statistics periodically. see -b option.")
pa.add_argument("-b", action="store", dest="break_word", default="GGA",
               help="specify a word to break the stream input.")
pa.add_argument("--minimum-snr", action="store", dest="min_snr", default=32,
               help="specify the minimum SNR for an external application.")
pa.add_argument("-v", action="store_true", dest="verbose",
               help="enable verbose mode.")
pa.add_argument("-d", action="store_true", dest="debug",
               help="enable debug mode.")
opt = pa.parse_args()

def print_stat(result):
    if result is None:
        return
    print("## {}".format(datetime.now()))
    print("Satellites in view: {}".format(result["n_view"]))
    print("Satellites in tracking: {}".format(len(result["tracked"])))
    print("Satellites in good signal: {}".format(len(result["n_good"])))

'''
main
'''
nmea = nmea_parser()

line_no = 0

if opt.break_mode:
    for line in sys.stdin:
        line_no += 1
        if line[3:6] == opt.break_word:
            print_stat(nmea.eval(min_snr=opt.min_snr))
            nmea.init()
        if nmea.append(line) == False:
            if opt.verbose:
                print("line {}: {}".format(line_no, nmea.strerror()))
    # it doesn't reach here.
    exit(0)

#
# non break_mode
#
data = sys.stdin.read()

for line in data.split("\n"):
    line_no += 1
    if nmea.append(line) == False:
        if opt.debug or opt.verbose:
            print("line {}: {}".format(line_no, nmea.strerror()))

result = nmea.eval(min_snr=32)

if opt.debug:
    print(json.dumps(nmea.get(),indent=4))
    print(json.dumps(result,indent=4))

print_stat(result)

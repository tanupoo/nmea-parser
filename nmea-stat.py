#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import argparse
from datetime import datetime
import json
from nmea_parser import nmea_parser

MIN_SNR=32

pa = argparse.ArgumentParser(description="a parser of the NMEA messages.")
pa.add_argument("-g", action="store_true", dest="show_geom",
               help="enable to show the geometric parameters.")
pa.add_argument("-c", action="store_true", dest="show_cond",
               help="enable to show the condition of satelliates.")
pa.add_argument("-s", action="store_true", dest="stream_mode",
               help="enable to show a statistics periodically. see -b option.")
pa.add_argument("-b", action="store", dest="break_word", default="GGA",
               help="specify a word to break the stream input.")
pa.add_argument("-f", action="store", dest="input_file", default="-",
               help="specify the file name of NMEA messages.")
pa.add_argument("--min-snr", action="store", dest="min_snr", default=MIN_SNR,
                type=int,
                help="specify the minimum SNR for an external application.")
pa.add_argument("--ignore-cksum", action="store_true", dest="ignore_cksum",
               help="specify to ignore the check sum.")
pa.add_argument("-v", action="store_true", dest="verbose",
               help="enable verbose mode.")
pa.add_argument("-d", action="store_true", dest="debug",
               help="enable debug mode.")
opt = pa.parse_args()

def print_cond(result):
    if result is None:
        return
    print("## {}".format(datetime.now()))
    print("Satellites in view: {}".format(result["n_view"]))
    print("Satellites in tracking: {}".format(len(result["tracked"])))
    print("Satellites in good signal: {}".format(len(result["n_good"])))

def print_geom(result):
    print("## {}".format(datetime.now()))
    print("  Statis: {}".format(result["status"]))
    print("  UTC: {}".format(result["datetime"]))
    print("  Latitude: {}".format(result["latitude"]))
    print("  Longitude: {}".format(result["longitude"]))
    print("  Altitude: {}".format(result["altitude"]))
    print("  Height of geoid: {}".format(result["height"]))
    print("  Speed: {}".format(result["speed"]))
    print("  Angle: {}".format(result["angle"]))
    print("  Quality: {}".format(result["quality"]))
    print("  Mode: {}".format(result["mode"]))
    print("  Tracked: {}".format(result["n_tracked"]))
    print("  PDOP: {}".format(result["pdop"]))
    print("  HDOP: {}".format(result["hdop"]))
    print("  VDOP: {}".format(result["vdop"]))

def show_result(nmea):
    if opt.show_cond:
        result = nmea.eval(min_snr=opt.min_snr)
        if result is None:
            if opt.verbose:
                print(nmea.strerror())
            return
        if opt.debug:
            print("## cond:\n", json.dumps(result,indent=4))
        print_cond(result)
    elif opt.show_geom:
        result = nmea.get_geom()
        if result is None:
            if opt.verbose:
                print(nmea.strerror())
            return
        if opt.debug:
            print("## geom:\n", json.dumps(result,indent=4))
        print_geom(result)
    else:
        print(json.dumps(nmea.get(),indent=4))

def main_loop(fd):
    nmea = nmea_parser(pedantic=not opt.ignore_cksum)

    line_no = 0

    if opt.stream_mode:
        # stream mode
        for line in fd:
            line_no += 1
            if line[3:6] == opt.break_word:
                show_result(nmea)
                nmea.init()
            if nmea.append(line) == False:
                if opt.verbose:
                    print("line {}: {}".format(line_no, nmea.strerror()))
        # it doesn't reach here.
    else:
        # non stream mode
        data = fd.read()

        for line in data.split("\n"):
            line_no += 1
            if nmea.append(line) == False:
                if opt.verbose:
                    print("line {}: {}".format(line_no, nmea.strerror()))
        # show result.
        show_result(nmea)

'''
main
'''
if opt.input_file == "-":
    main_loop(sys.stdin)
else:
    with open(opt.input_file) as fd:
        main_loop(fd)


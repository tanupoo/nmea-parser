nmea-parser
===========

pynmea2 is a good parser.  However, the output is not suitable for my use.
That's is why I make another parser here.

- nmea-stat.py is a tool.
- nmea_parser.py is a class to parse the NMEA message.

## USAGE

    usage: nmea-stat.py [-h] [-g] [-c] [-s] [-b BREAK_WORD] [-f INPUT_FILE]
                        [--min-snr MIN_SNR] [-v] [-d]
    
    optional arguments:
      -h, --help         show this help message and exit
      -g                 enable to show the geometric parameters.
      -c                 enable to show the condition of satelliates.
      -s                 enable to show a statistics periodically. see -b option.
      -b BREAK_WORD      specify a word to break the stream input.
      -f INPUT_FILE      specify the file name of NMEA messages.
      --min-snr MIN_SNR  specify the minimum SNR for an external application.
      -v                 enable verbose mode.
      -d                 enable debug mode.

- one time parser.

You can see the NMEA data in JSON.

    % nmea-stat.py -f nmea.txt

or

    % cat nmea.txt | nmea-stat.py

You can see the condition of the satellites in the device's sight.

    % cat nmea.txt | nmea-stat.py -c

- streaming mode.

    % cat /dev/tty.BT-GPS-32D4BF-BT-GPSCOM | nmea-stat.py -s -c
    ## 2018-09-23 16:05:35.882785
    Satellites in view: 0
    Satellites in tracking: 8
    Satellites in good signal: 0
    ## 2018-09-23 16:05:35.888776
    Satellites in view: 0
    Satellites in tracking: 8
    Satellites in good signal: 0
    ## 2018-09-23 16:05:35.894978
    Satellites in view: 8
    Satellites in tracking: 8
    Satellites in good signal: 3
    ## 2018-09-23 16:05:35.898623
    Satellites in view: 0
    Satellites in tracking: 8
    Satellites in good signal: 0

## BUGS

I have implemented only NMEA messages I need.
Other messages might be added in the future.

## REFERENCES

- https://www.gpsinformation.org/dale/nmea.htm
- http://freenmea.net/docs

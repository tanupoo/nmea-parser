nmea-parser
===========

pynmea2 is a good parser.  However, the output is not suitable for my use.
That's is why I make another parser here.

- nmea-stat.py is a tool.
- nmea_parser.py is a class to parse the NMEA message.

## USAGE

- one time parser.

    % cat sample/1.txt | nmea-stat.py
    ## 2018-09-23 16:06:59.529588
    Satellites in view: 21
    Satellites in tracking: 17
    Satellites in good signal: 12

if you add the -d option, you can see the NMEA data in JSON.

- streaming mode.

    % cat /dev/tty.BT-GPS-32D4BF-BT-GPSCOM | nmea-stat.py -B
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

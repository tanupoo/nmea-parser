nmea-parser
===========

pynmea2 is a good parser.  However, the output is not suitable for my use.
That's is why I make another parser here.

- nmea-stat.py is a tool.
- nmea_parser.py is a class to parse the NMEA message.

## USAGE

It doesn't show any error messages.
If you see something strange output, you can add -v option,
then you can see what happens during parsing.

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

### One time mode.

You can see the NMEA data in JSON.

    % nmea-stat.py -f nmea.txt

or

    % cat nmea.txt | nmea-stat.py

You can specify the device file as the file name.  See the streaming mode.

With the -c option, you can see the condition of the satellites in the device's sight.

    % nmea-stat.py --ignore-cksum --min-snr=35 -c
    ## 2018-09-24 07:55:32.294942
      Satellites in view: 10
      Satellites in tracking: 5
      Satellites in good signal: 3

The time stamp of each header is the time when you parse the data,
If you want to know the date and time when the data was taken,
you should add the -g option to see the geometric data.

With the -g option, you can see the geometric data of the GPS device.

    % nmea-stat.py --ignore-cksum -g
    ## 2018-09-24 07:57:13.800630
      Statis: A
      UTC: 2003-04-22 00:14:30.003
      Latitude: 39.1231417
      Longitude: -120.9587217
      Altitude: 00545.5 M
      Height of geoid: -26.0 M
      Speed: 0.0
      Angle: 175.3
      Quality: GPS fix
      Mode: 3D fix
      Tracked: 5
      PDOP: Good (04.5)
      HDOP: Good (02.1)
      VDOP: Good (04.0)

### Streaming mode.

You can see the result continuously if you add the -s option.
Either -c and -g options can be used.

    % nmea-stat.py -s -c -f /dev/tty.BT-GPS-32D4BF-BT-GPSCOM

## BUGS

I have implemented only NMEA messages I need.
Other messages might be added in the future.

## REFERENCES

- https://www.gpsinformation.org/dale/nmea.htm
- http://freenmea.net/docs

# -*- coding: utf-8 -*-

def verify_cksum(src):
    if len(src) == 0 or src[0] != "$":
        return False
    if len(src.split("*")) == 1:
        # there is no "*".  avoiding to through raise by index("*")
        return False
    base, cksum = src[1:].split("*")
    if len(cksum) == 0:
        return False
    res = 0
    for c in [base[i] for i in range(0,len(base))]:
        if c == "$":
            continue
        res ^= ord(c)
    return hex(res&0xff)[2:] == cksum.lower()

class nmea_parser():

    def __init__(self):
        self.init()
        self.__func = {
            "RMC": self.parse_RMC,
            "VTG": self.parse_VTG,
            "GGA": self.parse_GGA,
            "GSA": self.parse_GSA,
            "GSV": self.parse_GSV,
            "GLL": self.parse_GLL,
            "ZDA": self.parse_ZDA,
        }

    def __str__(self):
        return "{}".format(self.talkers)

    def init(self):
        self.talkers = {}
        self.condition = {}
        self.__error_msg = ""

    def get(self, *arg):
        return self.talkers

    def strerror(self):
        return self.__error_msg

    def append(self, line):
        line = line.strip()
        if len(line) == 0:
            self.__error_msg = "no data"
            return False
        if line[0] != "$":
            self.__error_msg = "not NMEA data"
            return False
        '''
        if verify_cksum(line) == False:
            self.__error_msg = "check sum error"
            return False
        '''
        f = self.__func.get(line[3:6])
        if f:
            if f(line) == False:
                self.__error_msg = "not enough items."
                return False
        else:
            self._error_msg = "unknown NMEA message."
            return False
        #
        return True

    def conv_dmm_deg(self, src, d):
        '''
        src: a string, not a float.
        XXX need to check a negative value of longitude.
        '''
        i = src.index(".")-2
        if d in [ "S", "W" ]:
            sign = -1
        else:
            sign = 1
        return sign * float(src[:i]) + round(float(src[i:])/60,7)

    def get_keys(self, msg):
        '''
        msg
            "   $GPGSV,2,1,,,22,45*75   "
        is gonna be 
            "GPGSV,2,1,,,22,45"
        then, it is splitted.
        Now, it supports a string, of which check sum is not correct,
        and which "*" is missed.
        '''
        item = msg.strip().split("*")[0][1:]
        talker_id = item[0][:2]
        return talker_id, item

    def parse_GSV(self, msg):
        '''
        e.g.
        $GPGSV,2,1,08,01,40,083,46,02,17,308,41,12,07,344,39,14,22,228,45*75
        '''
        talker_id, item = self.get_keys(msg)
        v = []
        for i in range(4,len(item)):
            if i%4 == 0:
                s = {"prn":item[i]}
                v.append(s)
            elif i%4 == 1:
                s["elevation"] = item[i]
            elif i%4 == 2:
                s["azimuth"] = item[i]
            elif i%4 == 3:
                s["snr"] = item[i]
        # even if some items are missed in the line,
        # when the check sum of the line is correct,
        # it should not be an error
        t = self.talkers.setdefault(talker_id,{})
        sv = t.setdefault("GSV", { "n_talkers":item[3],
                                  "sentences":[0]*int(item[1]),
                                  "talkers":[] })
        sv["sentences"][int(item[2])-1] = msg
        sv["talkers"].extend(v)

    def parse_GSA(self, msg):
        '''
        e.g.
        GPGSA,A,3,04,05,,09,12,,,24,,,,,2.5,1.3,2.1
        '''
        talker_id, item = self.get_keys(msg)
        t = self.talkers.setdefault(talker_id,{})
        sv = t.setdefault("GSA",{})
        sv["sentence"] = msg
        sv["pdop"] = item[15]
        sv["hdop"] = item[16]
        sv["vdop"] = item[17]
        tracked = sv.setdefault("tracked",[])
        tracked.extend(item[3:15])

    def parse_GGA(self, msg):
        '''
        e.g.
        $GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
        '''
        talker_id, item = self.get_keys(msg)
        t = self.talkers.setdefault(talker_id,{})
        sv = t.setdefault("GGA", {})
        sv["sentence"] = msg
        sv["utc"] = "{}:{}:{}".format(item[1][:2],item[1][2:4],item[1][4:])
        sv["latitude"] = self.conv_dmm_deg(item[2], item[3])
        sv["longitude"] = self.conv_dmm_deg(item[4], item[5])
        sv["quality"] = item[6]
        sv["n_tracked"] = item[7]
        sv["h_dilution"] = item[8]
        sv["altitude"] = "{} {}".format(item[9], item[10])
        sv["height"] = "{} {}".format(item[11], item[12])
        sv["dgps_update"] = item[13]
        sv["dgps_id"] = item[14]

    def parse_RMC(self, msg):
        '''
        e.g.
        $GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
        '''
        talker_id, item = self.get_keys(msg)
        t = self.talkers.setdefault(talker_id,{})
        sv = t.setdefault("RMC", {})
        sv["sentence"] = msg
        sv["utc"] = "{}:{}:{}".format(item[1][:2],item[1][2:4],item[1][4:])
        sv["status"] = item[2]
        sv["latitude"] = self.conv_dmm_deg(item[3],item[4])
        sv["longitude"] = self.conv_dmm_deg(item[5],item[6])
        sv["speed"] = float(item[7])
        sv["angle"] = item[8]
        sv["date"] = "20{}-{}-{}".format(item[9][:2],item[9][2:4],item[9][4:])
        sv["magnetic"] = "{} {}".format(item[10], item[11])

    def parse_GLL(self, msg):
        '''
        e.g.
        $GPGLL,4916.45,N,12311.12,W,225444,A,*1D
        '''
        talker_id, item = self.get_keys(msg)
        t = self.talkers.setdefault(talker_id,{})
        sv = t.setdefault("GLL", {})
        sv["sentence"] = msg
        sv["latitude"] = self.conv_dmm_deg(item[1],item[2])
        sv["longitude"] = self.conv_dmm_deg(item[3],item[4])
        sv["utc"] = "{}:{}:{}".format(item[5][:2],item[5][2:4],item[5][4:])

    def parse_VTG(self, msg):
        '''
        e.g.
        $GPVTG,054.7,T,034.4,M,005.5,N,010.2,K*48
        XXX the order of each T,M,N,K is fixed ?
        '''
        talker_id, item = self.get_keys(msg)
        t = self.talkers.setdefault(talker_id,{})
        sv = t.setdefault("VTG", {})
        sv["sentence"] = msg
        sv["true_track"] = "{}".format(item[1])
        sv["magnetic_track"] = "{}".format(item[3])
        sv["ground_speed_knots"] = "{}".format(item[5])
        sv["ground_speed_kmph"] = "{}".format(item[7])

    def parse_ZDA(self, msg):
        '''
        e.g.
        $GPZDA,201530.00,04,07,2002,00,00*60
        '''
        talker_id, item = self.get_keys(msg)
        t = self.talkers.setdefault(talker_id,{})
        sv = t.setdefault("ZDA", {})
        sv["sentence"] = msg
        sv["utc"] = "{}:{}:{}".format(item[1][:2],item[1][2:4],item[1][4:])
        sv["date"] = "{}-{}-{}".format(item[4],item[3],item[2])
        sv["tz"] = "{}:{}".format(item[5],item[6])

    def eval(self, min_snr=None):
        '''
        evaluation the input.
        '''
        gn = self.talkers.get("GN")
        if not gn:
            return None
        gsa = gn.get("GSA")
        if not gsa:
            return None
        gp = self.talkers.get("GP")
        if not gp:
            return None
        gsv = gp.get("GSV")
        if not gsv:
            return None
        talkers = gsv.get("talkers")
        if not talkers:
            return None
        #
        tracked = self.condition.setdefault("tracked",[])
        v = []
        for i in gsa.get("tracked"):
            if not i:
                continue
            tracked.append(i)
            for j in talkers:
                if i == j.get("prn"):
                    if min_snr is not None:
                        snr = j.get("snr")
                        if not snr:
                            snr = 0
                        else:
                            snr = int(snr)
                        if snr <= min_snr:
                            continue
                    #
                    v.append(j)
        self.condition["n_good"] = v
        # find GSV and n_talkers.
        n_view = 0
        for i in self.talkers.keys():
            gsv = self.talkers[i].get("GSV")
            if gsv:
                n = gsv.get("n_talkers")
                if n:
                    n_view += int(n)
        self.condition["n_view"] = n_view
        #
        return self.condition

'''
main
'''
if __name__ == "__main__" :
    import sys
    import json

    if len(sys.argv) == 1:
        data = sys.stdin.read()
    else:
        data = """
            $GNRMC,084840.00,A,2343.01835,N,10720.13551,E,0.010,,180918,,,A*68
            $GNVTG,,T,,M,0.010,N,0.018,K,A*35
            $GNGGA,084840.00,2343.01835,N,10720.13551,E,1,12,0.62,116.4,M,38.8,M,,*4A
            $GNGSA,A,3,05,29,02,21,28,24,13,30,15,,,,1.17,0.62,0.99*19
            $GNGSA,A,3,76,67,66,82,83,81,75,77,,,,,1.17,0.62,0.99*15
            $GPGSV,3,1,10,02,18,172,33,05,56,098,35,13,66,016,30,15,53,285,52*78
            $GPGSV,3,2,10,20,02,305,,21,26,310,35,24,30,202,38,28,11,077,15*7C
            $GPGSV,3,3,10,29,07,245,42,30,19,044,35*7C
            $GLGSV,3,1,10,65,05,090,08,66,47,044,33,67,41,323,42,68,00,288,*6E
            $GLGSV,3,2,10,75,13,029,29,76,45,067,32,77,35,153,25,81,18,219,25*6E
            $GLGSV,3,3,10,82,32,272,41,83,17,325,36*61
            $GNGLL,2343.01835,N,10720.13551,E,084840.00,A,A*79
            $GNZDA,084840.00,18,09,2018,00,00*73
        """

    nmea = nmea_parser()

    line_no = 0
    for line in data.split("\n"):
        line_no += 1
        if nmea.append(line) == False:
            print("line {}: {}".format(line_no, nmea.strerror()))

    print(json.dumps(nmea.get(),indent=4))
    result = nmea.eval(min_snr=32)
    print(json.dumps(result,indent=4))
    #
    print("Satellites in view: {}".format(result["n_view"]))
    print("Satellites in tracking: {}".format(len(result["tracked"])))
    print("Satellites in good signal: {}".format(len(result["n_good"])))


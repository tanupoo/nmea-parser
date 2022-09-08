# -*- coding: utf-8 -*-

def verify_cksum(src):
    if len(src) == 0 or src[0] != "$":
        return False
    if len(src.split("*")) == 1:
        # there is no "*".  avoiding to through raise by index("*")
        return False
    try:
        # 
        base, cksum = src[1:].split("*")
    except ValueError as e:
        if "too many values to unpack" in str(e):
            print("ERROR: ignore invalid line, more than one * exist.")
            return False
        else:
            raise
    if len(cksum) == 0:
        return False
    res = 0
    for c in [base[i] for i in range(0,len(base))]:
        if c == "$":
            continue
        res ^= ord(c)
    return hex(res&0xff)[2:] == cksum.lower()

def get_str_dop(v):
    '''
    convert a DOP value in GGA or GSA into a string.
    https://en.wikipedia.org/wiki/Dilution_of_precision_(navigation)#Meaning_of_DOP_Values
    '''
    if v > 0 and v < 1:
        return "Ideal"
    if v < 2:
        return "Excellent"
    if v < 5:
        return "Good"
    if v < 10:
        return "Moderate"
    if v < 20:
        return "Fair"
    return "Poor"

def get_str_quality(v):
    '''
    convert a fix value in GGA into a string.
    '''
    if v == 0 or v > 8:
        return "unknown"
    #
    return [ "GPS fix", "DGPS fix", "PPS fix", "Real Time",
        "Float RTK", "estimated", "Manual", "Simulation mode" ][v-1]

def get_str_mode(v):
    '''
    convert a mode value in GSA into a string.
    '''
    if v == 0 or v > 3:
        return "unknown"
    return [ "no fix", "2D fix", "3D fix" ][v-1]

class nmea_parser():

    def __init__(self, ignore_cksum=False):
        self.ignore_cksum = ignore_cksum
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
        return "{}".format(self.nmea_obj)

    def init(self):
        self.nmea_obj = {}
        self.condition = {}
        self.geometry = {}
        self.__error_msg = ""

    def get(self, *arg):
        return self.nmea_obj

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
        if not self.ignore_cksum:
            if verify_cksum(line) == False:
                self.__error_msg = "check sum error"
                return False
        f = self.__func.get(line[3:6])
        if f:
            if f(line) == False:
                self.__error_msg = "not enough items."
                return False
        else:
            self.__error_msg = "unknown NMEA message."
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

    def get_items(self, msg, nitems=0, required=[]):
        '''
        msg
            "   $GPGSV,2,1,,,22,45*75   "
        is gonna be 
            "GPGSV,2,1,,,22,45"
        then, it is splitted.
        Now, it supports a string, of which check sum is not correct,
        and which "*" is missed.
        '''
        item = msg.strip().split("*")[0][1:].split(",")
        talker_id = item[0][:2]
        if nitems and len(item) < nitems:
            item.append([""]*(nitems-len(item)))
        for i in required:
            if item[i] == "":
                return talker_id, i
        return talker_id, item

    def get_key(self, name):
        target = None
        for i in ["GN", "GP"]:
            g = self.nmea_obj.get(i)
            if g is None:
                continue
            target = g.get(name)
            if target:
                break
        return target

    def parse_GSV(self, msg):
        '''
        even if some items are missed in the line,
        when the check sum of the line is correct,
        it should not be an error.
        e.g.
        $GPGSV,2,1,08,01,40,083,46,02,17,308,41,12,07,344,39,14,22,228,45*75
        '''
        talker_id, item = self.get_items(msg)
        v = []
        for i in range(4,len(item)):
            if i%4 == 0:
                s = {"prn":item[i], "elevation":0, "azimuth":0, "snr":0}
                v.append(s)
            elif i%4 == 1:
                s["elevation"] = item[i]
            elif i%4 == 2:
                s["azimuth"] = item[i]
            elif i%4 == 3:
                s["snr"] = item[i]
        t = self.nmea_obj.setdefault(talker_id,{})
        sv = t.setdefault("GSV", { "n_talkers":item[3],
                                  "sentences":['']*int(item[1]),
                                  "talkers":{} })
        try:
            sv["sentences"][int(item[2])-1] = msg
        except IndexError:
            a = len(sv["sentences"])
            b = int(item[2])-1
            self.__error_msg = f"sentences was too short {a} for {b}"
            return False
        for i in v:
            if sv["talkers"].get(i["prn"]):
                self.__error_msg = "{} exists already in GSV.".format(i["prn"])
                return False
            sv["talkers"][i["prn"]] = i
            sv["talkers"][i["prn"]].pop("prn")
        return True

    def parse_GSA(self, msg):
        '''
        e.g.
        GPGSA,A,3,04,05,,09,12,,,24,,,,,2.5,1.3,2.1
        '''
        talker_id, item = self.get_items(msg)
        t = self.nmea_obj.setdefault(talker_id,{})
        sv = t.setdefault("GSA",{})
        sv["sentence"] = msg
        sv["selection_mode"] = item[1]
        sv["mode"] = item[2]
        sv["pdop"] = item[15]
        sv["hdop"] = item[16]
        sv["vdop"] = item[17]
        tracked = sv.setdefault("tracked",{})
        for i in item[3:15]:
            if i:
                tracked.setdefault(i, True)
        return True

    def parse_GGA(self, msg):
        '''
        e.g.
        $GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
        '''
        talker_id, item = self.get_items(msg, nitems=15,
                                         required=[2,3,4,5,9,10,11,12])
        if isinstance(item, int):
            print(f"ERROR: GGA item {item} is empty: {msg}")
            return False
        t = self.nmea_obj.setdefault(talker_id,{})
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
        return True

    def parse_RMC(self, msg):
        '''
        e.g.
        $GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
        '''
        talker_id, item = self.get_items(msg,
                                         required=[3,4,5,6,7])
        if isinstance(item, int):
            print(f"ERROR: RMC item {item} is empty: {msg}")
            return False
        t = self.nmea_obj.setdefault(talker_id,{})
        sv = t.setdefault("RMC", {})
        sv["sentence"] = msg
        sv["utc"] = "{}:{}:{}".format(item[1][:2],item[1][2:4],item[1][4:])
        sv["status"] = item[2]
        sv["latitude"] = self.conv_dmm_deg(item[3],item[4])
        sv["longitude"] = self.conv_dmm_deg(item[5],item[6])
        sv["speed"] = float(item[7])
        sv["angle"] = item[8]
        sv["date"] = "20{}-{}-{}".format(item[9][4:],item[9][2:4],item[9][:2])
        sv["magnetic"] = "{} {}".format(item[10], item[11])
        return True

    def parse_GLL(self, msg):
        '''
        e.g.
        $GPGLL,4916.45,N,12311.12,W,225444,A,*1D
        '''
        talker_id, item = self.get_items(msg,
                                         required=[1,2,3,4])
        if isinstance(item, int):
            print(f"ERROR: GLL item {item} is empty: {msg}")
            return False
        t = self.nmea_obj.setdefault(talker_id,{})
        sv = t.setdefault("GLL", {})
        sv["sentence"] = msg
        sv["latitude"] = self.conv_dmm_deg(item[1],item[2])
        sv["longitude"] = self.conv_dmm_deg(item[3],item[4])
        sv["utc"] = "{}:{}:{}".format(item[5][:2],item[5][2:4],item[5][4:])
        sv["status"] = item[6]
        return True

    def parse_VTG(self, msg):
        '''
        e.g.
        $GPVTG,054.7,T,034.4,M,005.5,N,010.2,K*48
        XXX the order of each T,M,N,K is fixed ?
        '''
        talker_id, item = self.get_items(msg)
        t = self.nmea_obj.setdefault(talker_id,{})
        sv = t.setdefault("VTG", {})
        sv["sentence"] = msg
        sv["true_track"] = "{}".format(item[1])
        sv["magnetic_track"] = "{}".format(item[3])
        sv["ground_speed_knots"] = "{}".format(item[5])
        sv["ground_speed_kmph"] = "{}".format(item[7])
        return True

    def parse_ZDA(self, msg):
        '''
        e.g.
        $GPZDA,201530.00,04,07,2002,00,00*60
        '''
        talker_id, item = self.get_items(msg)
        t = self.nmea_obj.setdefault(talker_id,{})
        sv = t.setdefault("ZDA", {})
        sv["sentence"] = msg
        sv["utc"] = "{}:{}:{}".format(item[1][:2],item[1][2:4],item[1][4:])
        sv["date"] = "{}-{}-{}".format(item[4],item[3],item[2])
        sv["tz"] = "{}:{}".format(item[5],item[6])
        return True

    def eval(self, min_snr=None):
        '''
        evaluation the input.
        '''
        # collect the talkers from each GSV.
        # and get the number of talkers from n_talkers.
        talkers = {}
        n_view = 0
        for i in self.nmea_obj.keys():
            gsv = self.nmea_obj[i].get("GSV")
            if gsv:
                talkers.update(gsv["talkers"])
                n = gsv.get("n_talkers")
                if n:
                    n_view += int(n)
        self.condition["n_view"] = n_view
        # find a GSA
        gsa = self.get_key("GSA")
        if gsa is None:
            self.__error_msg = "GGA doesn't exists."
            return None
        if gsa.get("tracked") is None:
            self.__error_msg = "tracked in GGA doesn't exists."
            return None
        tracked = self.condition.setdefault("tracked",[])
        n_good = []
        for i in gsa.get("tracked").keys():
            tracked.append(i)
            for j, k in talkers.items():
                if i != j:
                    continue
                if min_snr is not None:
                    snr = int(k.get("snr", 0))
                    if snr <= min_snr:
                        continue
                #
                n_good.append(j)
        self.condition["n_good"] = n_good
        #
        return self.condition

    def get_geom(self):
        rmc = self.get_key("RMC")
        if not rmc:
            self.__error_msg = "RMC doesn't exists."
            return None
        gga = self.get_key("GGA")
        if not gga:
            self.__error_msg = "GGA doesn't exists."
            return None
        gsa = self.get_key("GSA")
        if not gsa:
            self.__error_msg = "GSA doesn't exists."
            return None
        self.geometry["status"] = rmc["status"]
        self.geometry["datetime"] = "{} {}".format(rmc["date"], rmc["utc"])
        self.geometry["latitude"] = rmc["latitude"]
        self.geometry["longitude"] = rmc["longitude"]
        self.geometry["altitude"] = gga["altitude"]
        self.geometry["height"] = gga["height"]
        self.geometry["speed"] = rmc["speed"]
        self.geometry["angle"] = rmc["angle"]
        self.geometry["quality"] = get_str_quality(int(gga["quality"]))
        self.geometry["mode"] = get_str_mode(int(gsa["mode"]))
        self.geometry["n_tracked"] = int(gga["n_tracked"])
        self.geometry["pdop"] = "{} ({})".format(
                get_str_dop(float(gsa["pdop"])),gsa["pdop"])
        self.geometry["hdop"] = "{} ({})".format(
                get_str_dop(float(gsa["hdop"])),gsa["hdop"])
        self.geometry["vdop"] = "{} ({})".format(
                get_str_dop(float(gsa["vdop"])),gsa["vdop"])
        #
        return self.geometry


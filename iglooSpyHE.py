import hcal_teststand.ngfec
import hcal_teststand.hcal_teststand
from time import sleep
from optparse import OptionParser
import sys
from hcal_teststand.utilities import *

def readIglooSpy_per_card(port,crate, slot, card, Nsamples=0,ts=None):
    results = {}
    try:
        cmds1 = ["put HE{0}-{1}-{2}-i_CntrReg_WrEn_InputSpy 1".format(crate, slot, card),
                 "wait 100",
                 "put HE{0}-{1}-{2}-i_CntrReg_WrEn_InputSpy 0".format(crate, slot, card),
                 "get HE{0}-{1}-{2}-i_StatusReg_InputSpyWordNum".format(crate, slot, card)]
        print "put HE{0}-{1}-{2}-i_CntrReg_WrEn_InputSpy 1".format(crate, slot, card)
        print "put HE{0}-{1}-{2}-i_CntrReg_WrEn_InputSpy 0".format(crate, slot, card)
        output = hcal_teststand.ngfec.send_commands(ts=ts, port=port,cmds=cmds1, script=True)
        nsamples = int(output[-1]["result"],16) if not Nsamples else min(int(output[-1]["result"],16),Nsamples)
        #print "nsamples: ", int(nsamples,16)
        
        cmds2 = ["get HE{0}-{1}-{2}-i_inputSpy".format(crate, slot, card),
                 "wait 200"]*nsamples
#        print cmds2
        output_all = hcal_teststand.ngfec.send_commands(ts=ts, port=port, cmds=cmds2, script=True)
        #print output_all
        results[crate, slot, card] = [out["result"] for out in output_all if not (out["result"] == "OK" or out["result"] == "commented command")]
    except Exception as ex:
        print "Caught exception:"
        print ex
    return results        

def readIglooSpy(tsname):
    results = {}

    ts = hcal_teststand.hcal_teststand.teststand(tsname)
    for icrate, crate in enumerate(ts.fe_crates):
        for slot in ts.qie_slots[icrate]:
            for card in ts.qiecards[crate,slot]:
                try:
                    cmds1 = ["put HE{0}-{1}-{2}-i_CntrReg_WrEn_InputSpy 1".format(crate, slot, card),
                             "wait 100",
                             "put HE{0}-{1}-{2}-i_CntrReg_WrEn_InputSpy 0".format(crate, slot, card),
                             "get HE{0}-{1}-{2}-i_StatusReg_InputSpyWordNum".format(crate, slot, card)]

                    print cmds1
                    output = hcal_teststand.ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
                    print output
                    nsamples = output[-1]["result"]
                    #print "nsamples: ", int(nsamples,16)

                    cmds2 = ["get HE{0}-{1}-{2}-i_inputSpy".format(crate, slot, card),
                             "wait 200"]*(int(nsamples,16))
                    #cmds2 = ["get HE{0}-{1}-{2}-i_inputSpy".format(crate, slot, card),
                    #         "wait 200"]*(10)
                    print cmds2
                    output_all = hcal_teststand.ngfec.send_commands(ts=ts, cmds=cmds2, script=True)
                    #print output_all
                    results[crate, slot, card] = [out["result"] for out in output_all if not (out["result"] == "OK" or out["result"] == "commented command")]
                except Exception as ex:
                    print "Caught exception:"
                    print ex
                    #just continue with the next one
    return results

def interleave(c0, c1):
    retval = 0;
    for i in xrange(8):
        bitmask = 0x01 << i
        retval |= ((c0 & bitmask) | ((c1 & bitmask) << 1)) << i;

    return retval

def parseIglooSpy(buff):
    # first split in pieces
    buff_l = buff.split()
    qie_info = []
    # Sometimes the reading wasn't complete, so put some safeguards
    if len(buff_l) > 1:
        counter = buff_l[0]
        for elem in buff_l[1:]:
            # check that it's long enough
            if len(elem) == 10:
                qie_info.append(elem[:6])
                qie_info.append("0x"+elem[6:])

    return qie_info

def getInfoFromSpy_per_QIE(buff, verbose=False):

    BITMASK_TDC = 0x07
    OFFSET_TDC0 = 4
    OFFSET_TDC1 = 4+8

    BITMASK_ADC = 0x07
    OFFSET_ADC0 = 1
    OFFSET_ADC1 = 1+8

    BITMASK_EXP = 0x01
    OFFSET_EXP0 = 0
    OFFSET_EXP1 = 0+8

    BITMASK_CAP = 0x01
    OFFSET_CAP0 = 7
    OFFSET_CAP1 = 15

    int_buff = int(buff,16)

    if verbose:
        # get binary representation
        buff_bin = bin(int_buff)
        print "{0} -> {1}".format(buff, buff_bin)

    adc1 = int_buff >> OFFSET_ADC1 & BITMASK_ADC
    adc0 = int_buff >> OFFSET_ADC0 & BITMASK_ADC
    adc = interleave(adc0, adc1)

    tdc1 = int_buff >> OFFSET_TDC1 & BITMASK_TDC
    tdc0 = int_buff >> OFFSET_TDC0 & BITMASK_TDC
    tdc = interleave(tdc0, tdc1)

    exp1 = int_buff >> OFFSET_EXP1 & BITMASK_EXP
    exp0 = int_buff >> OFFSET_EXP0 & BITMASK_EXP
    exp = interleave(exp0, exp1)

    c0 = int_buff >> OFFSET_CAP0 & BITMASK_CAP
    c1 = int_buff >> OFFSET_CAP1 & BITMASK_CAP
    capid = interleave(c0, c1)

    if verbose:
        print "adc_0:", adc0, "; adc_1:", adc1, "; adc:", adc
        print "exp_0:", exp0, "; exp_1:", exp1, "; exp:", exp
        print "tdc_0:", tdc0, "; tdc_1:", tdc1, "; tdc:", tdc
        print "capid_0:", c0, "; capid_1:", c1, "; capid:", capid


    #print buff, capid
    return {'capid':capid,
            'adc':adc,
            'exp':exp,
            'tdc':tdc}

def getInfoFromSpy_per_card(port,crate, slot, card, verbose=False, Nsamples=None, ts=None):
    output={}
    spyconts=readIglooSpy_per_card(port,crate, slot, card, Nsamples,ts)
    for spycontst in spyconts.values()[0]:
        outdire={}
        spycont=spycontst.split()
        nqie=0
        if verbose: print '\nspy_word #{0}\n'.format(int(spycont[0],16)),
        for sc in spycont[1:]:
            outdire['qie{0}'.format(nqie)]=getInfoFromSpy_per_QIE(sc[:-4]) if len(sc)>6 else getInfoFromSpy_per_QIE('0x0')
            if verbose: print 'qie{0}\t'.format(nqie),outdire['qie{0}'.format(nqie)]
            nqie+=1
            outdire['qie{0}'.format(nqie)]=getInfoFromSpy_per_QIE(sc[-4:]) if len(sc)>6 else (getInfoFromSpy_per_QIE(sc) if len(sc)>2 else getInfoFromSpy_per_QIE('0x0'))
            if verbose: print 'qie{0}\t'.format(nqie),outdire['qie{0}'.format(nqie)]
            nqie+=1
        output['spy{0}'.format(int(spycont[0],16))]=outdire
    if verbose:
        leftn=hcal_teststand.ngfec.send_commands(ts=None, port=port,cmds=["get HE{0}-{1}-{2}-i_StatusReg_InputSpyWordNum".format(crate, slot, card)], script=True)[0]
        print '\n',leftn['cmd'],'#',leftn['result']
    print 'NOTE THAT THE SPY FIFO WILL RETAIN OLD DATA UNTIL YOU FLUSH IT OR RESET IT !'
    return output

## -------------------------------------
## -- Get the info on adc, capid, tdc --
## -- from the list of registers.     --
## -------------------------------------

def getInfoFromSpy(buff_list):
    # get separate QIE info
    parsed_info_list = []
    for i, reading in enumerate(buff_list):
        #print "parsing", i, reading
        qie_info = parseIglooSpy(reading)
        # at this point qie_info could be zero, or less than 12 items long
        # Need to be able to deal with this
        parsed_info = []
        for info in qie_info:
            parsed_info.append(getInfoFromSpy_per_QIE(info))
        parsed_info_list.append(parsed_info)
        #print parsed_info

    return parsed_info_list

## ----------------------
## -- Check the capids --
## ----------------------

def capidOK(parsed_info):
    capids = set()
    for info in parsed_info:
        capid = info['capid']
        capids.add(capid)

    #print capids
    return len(capids) == 1, capids

def checkCapid(prev, curr):
    result = True
    error = []
    if prev != -1:
        if prev == 3:
            if curr != 0:
                result = False
                error.append("Capid did not rotate correctly. Previously it was {0}, now it is {1}.".format(prev, curr))
            elif prev in [0,1,2]:
                if curr - prev != 1:
                    result = False
                    error.append("Capid did not rotate correctly. Previously it was {0}, now it is {1}.".format(prev, curr))
            else:
                result = False
                error.append("Previous capid value ({0}) does not make sense.".format(prev))
    return result, error

def capidRotating(parsed_info_list):
    # check what the capid is for each reading, 
    # and make sure that the rotation is ok
    prev_capid = -1
    result = True
    error = []
    for i, parsed_info in enumerate(parsed_info_list):
        # parsed_info could be empty, or contain less than 12 items
        if len(parsed_info) == 0:
            # assume that all was fine
            if prev_capid != -1:
                if prev_capid == 3:
                    prev_capid = 0
                elif prev_capid in [0,1,2]:
                    prev_capid += 1

        else:
            # Check whether the capids were all the same
            capid = capidOK(parsed_info)
            if not capid[0]:
                result = False
                error.append("Not all capids were the same.")
            else:
                capid_value = list(capid[1])[0]
                if prev_capid != -1:
                    if prev_capid == 3:
                        if capid_value != 0:
                            result = False
                            error.append("Capid did not rotate correctly. Previously it was {0}, now it is {1}. (Line {2})".format(prev_capid, capid_value, i))
                    elif prev_capid in [0,1,2]:
                        if capid_value - prev_capid != 1:
                            result = False
                            error.append("Capid did not rotate correctly. Previously it was {0}, now it is {1}. (Line {2})".format(prev_capid, capid_value, i))
                    else:
                        result = False
                        error.append("Previous capid value ({0}) does not make sense.".format(prev_capid))
                
                prev_capid = capid_value

    return result, "\n".join(error)


if __name__ == "__main__":
    
    #bufflist = ['0x18 0x70f670f4 0x70f470f4 0x72f272f0 0x70f670f4 0x72f070f6 0x70f672f0',
    #            '0x17 0x70767274 0x70767272 0x70767074 0x70767074 0x70747270 0x70767272']

    parser = OptionParser()
    parser.add_option("--port", dest="port",
                      default=4342, type="int",
                      help="The ngCCM port number (default: %default)",
                      )
    parser.add_option("--crate", dest="crate",
                      default="0", type="string",
                      help="The crate string (default: 0)",
                      )
    parser.add_option("--slot", dest="slot",
                      default=0, type="int",
                      help="The slot string (default: 0)",
                      )
    parser.add_option("--card", dest="card",
                      default=0, type="int",
                      help="The card string (default: 0)",
                      )
    parser.add_option("--nsamples", dest="nsamples",
                      default=1, type="int",
                      help="number of samples to be read out (default: 1)",
                      )

    (options, args) = parser.parse_args()
    getInfoFromSpy_per_card(options.port,options.crate,options.slot,options.card,True,options.nsamples,None)




    
    

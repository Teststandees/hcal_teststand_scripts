import hcal_teststand.ngfec
import hcal_teststand.hcal_teststand
from time import sleep
from optparse import OptionParser
import sys
from hcal_teststand.utilities import *
import monitor_teststand

def readIglooSpy_per_card(port, crate, slot, topbottom, Nsamples=0,ts=None):
    results = {}
    if not (topbottom==0 or topbottom==1):
        print 'ERROR: parameter topbottom --- 1 for top, 0 for bottom'
        return results
    TB=['Bot','Top']
    try:
        cmd1 = ["put HF{0}-{1}-i{2}_CntrReg_WrEn_InputSpy 1".format(crate, slot, TB[topbottom]),
                "wait 100",
                "put HF{0}-{1}-i{2}_CntrReg_WrEn_InputSpy 0".format(crate, slot,TB[topbottom]),
                "get HF{0}-{1}-i{2}_StatusReg_InputSpyWordNum".format(crate, slot, TB[topbottom])]
        output = hcal_teststand.ngfec.send_commands(ts=ts, port=port,cmds=cmd1, script=True)
        nsamples = int(output[-1]["result"],16) if not Nsamples else min(int(output[-1]["result"],16),Nsamples) 
        cmd2 = ["get HF{0}-{1}-iTop_inputSpy".format(crate, slot, TB[topbottom]),
                 "wait 200"]*nsamples
#        print cmds2
        output_all = hcal_teststand.ngfec.send_commands(ts=ts, port=port, cmds=cmd2, script=True)
        #print output_all
        results[crate, slot, TB[topbottom]] = [out["result"] for out in output_all if not (out["result"] == "OK" or out["result"] == "commented command")]
    except Exception as ex:
        print "Caught exception:"
        print ex
    return results        

def readIglooSpy(tsname,numts):
    results = {}

    ts = hcal_teststand.hcal_teststand.teststand(tsname)

    for icrate, crate in enumerate(ts.fe_crates):
        for slot in ts.qie_slots[icrate]:
            try:
                print "######################################"
                print "# Getting info from HF{0} Slot {1} iTop #".format(crate, slot)
                print "######################################"
                cmds1 = ["put HF{0}-{1}-iTop_CntrReg_WrEn_InputSpy 1".format(crate, slot),
                         "wait 100",
                         "put HF{0}-{1}-iTop_CntrReg_WrEn_InputSpy 0".format(crate, slot),
                         "get HF{0}-{1}-iTop_StatusReg_InputSpyWordNum".format(crate, slot)]
                #print cmds1
                output = hcal_teststand.ngfec.send_commands(ts=ts, cmds=cmds1, script=True)#, time_out=200)
                for each in output:
                    print "Command: " + each['cmd'] + ", Result: " + each['result']
                #print output
                nsamples = output[-1]["result"]
                    #print "nsamples: ", int(nsamples,16)
                    # try to split things up in pieces
             
                cmds2 = []
                for i in range(numts):
                    cmds2.append("get HF{0}-{1}-iTop_inputSpy".format(crate, slot))
                    cmds2.append("wait 200")

                #cmds2 = ["get HF{0}-{1}-iTop_inputSpy".format(crate, slot),
                #         "wait 200"]*numts#(int(nsamples,16))
    
                
                while "wait" in cmds2[-1]:
                    cmds2 = cmds2[:-1]
                    #cmds2 = ["get HE{0}-{1}-{2}-i_inputSpy".format(crate, slot, card),

                output_all = hcal_teststand.ngfec.send_commands(ts=ts, cmds=cmds2, script=True)#, time_out=600)

                results[crate, slot] = [out["result"] for out in output_all if not out["result"] == "OK"]
                #print results
            except Exception as ex:
                print "Caught exception:"
                print ex
                    #just continue with the next one

    return results

def clear_buffer(tsname):

    ts = hcal_teststand.hcal_teststand.teststand(tsname)

    wrd_num = 512

    print "######################################"
    print "#  Clearing the buffer...            #"
    print "######################################"

    for icrate, crate in enumerate(ts.fe_crates):
        for slot in ts.qie_slots[icrate]:
            try:

                while wrd_num > 0:
    
                    wrdnum_cmd = "get HF{0}-{1}-iTop_StatusReg_InputSpyWordNum".format(crate, slot)

                    output_wrdnum = hcal_teststand.ngfec.send_commands(ts=ts, cmds=wrdnum_cmd, script=True)#, time_out=600)

                    wrd_num = int(output_wrdnum[0]['result'],16)

                    cmds3 = []
                    for i in range(wrd_num):
                        cmds3.append("get HF{0}-{1}-iTop_inputSpy".format(crate, slot))
                        cmds3.append("wait 200")
        
                #cmds2 = ["get HF{0}-{1}-iTop_inputSpy".format(crate, slot),
                #         "wait 200"]*numts#(int(nsamples,16))
        
                
                    while "wait" in cmds3[-1]:
                        cmds3 = cmds3[:-1]
                    #cmds2 = ["get HE{0}-{1}-{2}-i_inputSpy".format(crate, slot, card),
                    #         "wait 200"]*(10)
                    #         "wait 200"]*(10)

                    output_null = hcal_teststand.ngfec.send_commands(ts=ts, cmds=cmds3, script=True)#, time_out=600)

                    output_wrdnum = hcal_teststand.ngfec.send_commands(ts=ts, cmds=wrdnum_cmd, script=True)#, time_out=600)
    
                    print "Command: " + output_wrdnum[0]['cmd'] + ", Result: " + output_wrdnum[0]['result']
                    print "######################################"

                    wrd_num = int(output_wrdnum[0]['result'],16)

            except Exception as ex:
                print "Caught exception:"
                print ex
                    #just continue with the next one

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

def  getInfoFromSpy_per_card(port,crate, slot, isTop, verbose=False, Nsamples=None, ts=None):
    card=isTop
    if not (card==0 or card==1):
        print 'ERROR: parameter isTop --- 1 for top, 0 for bottom'
        return result
    TB=['Bot','Top']
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
        leftn=hcal_teststand.ngfec.send_commands(ts=None, port=port,cmds=["get HF{0}-{1}-i{2}_StatusReg_InputSpyWordNum".format(crate, slot, TB[card])], script=True)[0]
        print '\n',leftn['cmd'],'#',leftn['result']
    print 'NOTE THAT THE SPY FIFO WILL RETAIN OLD DATA UNTIL YOU FLUSH IT OR RESET IT !'
    return output

## -------------------------------------
## -- Get the info on adc, capid, tdc --
## -- from the list of registers.     --
## -------------------------------------

def getInfoFromSpy(buff_list,cid_only):
    # get separate QIE info
    parsed_info_list = []
    print "      ",
    for i in range(12):
        if cid_only == 1:
            print str(i).ljust(2),
        else:
            print "    " + str(i).rjust(2) + "      ",
    print ""
    print " TS : ",
    for i in range(12):
        if cid_only == 1:
            print "C ",
        else:
            print "C AD TD E | ",
    print ""
    for i, reading in enumerate(buff_list):
        print str(i).rjust(3) + " : ",
#        print "parsing", i, reading
        qie_info = parseIglooSpy(reading)
#        print qie_info
       # at this point qie_info could be zero, or less than 12 items long
        # Need to be able to deal with this
        if len(qie_info) == 12:
            parsed_info = []
            for info in qie_info:
                data = getInfoFromSpy_per_QIE(info)
                if cid_only == 1:
                    print str(data['capid']) + ' ',
                else:
                    print str(data['capid']) + ' ' + str(data['adc']).rjust(2) + ' ' + str(data['tdc']).rjust(2) + ' ' + str(data['exp']) + ' | ',
                parsed_info.append(getInfoFromSpy_per_QIE(info))
            print ""
            parsed_info_list.append(parsed_info)
        else:
            print "ACQUISITION ERROR"
#        print parsed_info

    return parsed_info_list
'''
def getInfoFromSpy(buff_list):
    # get separate QIE info
    parsed_info_list = []
    for i, reading in enumerate(buff_list):
        print "parsing", i, reading
        qie_info = parseIglooSpy(reading)
#        print qie_info
       # at this point qie_info could be zero, or less than 12 items long
        # Need to be able to deal with this
        parsed_info = []
        for info in qie_info:
            parsed_info.append(getInfoFromSpy_per_QIE(info))
        parsed_info_list.append(parsed_info)
        print parsed_info

    return parsed_info_list
'''

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
    parser.add_option("--sleep", dest="sleep",
                      default=10, metavar="N", type="float",
                      help="Sleep for %metavar minutes in between data runs (default: %default)",
                      )
    parser.add_option("-t", "--teststand", dest="tstype",
                      default = "igloo_spy",
                      type="string",
                      help="Which teststand to set up?"
                      )
    parser.add_option("-c", "--capidonly", dest="cid_only",
                      default = 0,
                      type="int",
                      help="1 = display CapID only,  0 = normal mode"
                      )
    parser.add_option("-n", "--numts", dest="numts",
                      default = 100,
                      type="int",
                      help="number of TS to capture -- 200 MAX"
                      )
    
    (options, args) = parser.parse_args()

    if not options.tstype:
        print "Please specify which teststand to use!"
        sys.exit()
    tstype = options.tstype

    try:
 #       while True:
        t_string = time_string()[:-4]
        path = "./spies/spy_{0}.txt".format(t_string)
            
        bufflist_dict = readIglooSpy(tstype,options.numts)
        
#        f = open(path,'w')
        #emailbody = ""
            
        for crate_slot, bufflist in bufflist_dict.iteritems():
         #   crate, slot = crate_slot
                #print crate, slot, card
         #   f.write("HF{0}, Slot {1}\n".format(crate, slot))
         #   f.write("Raw readings\n")
         #   f.write("\n".join(bufflist))
         #   f.write("\n")
                
                #f = open("testigloospy.txt")
                #bufflist = f.readlines()

            parsed_info_list = getInfoFromSpy(bufflist,options.cid_only)
            clear_buffer(tstype)
                #print parsed_info_list
                #f.write("Parsed info\n")
                #f.write("\n".join([",".join(info) for info in parsed_info_list]))
                #f.write("\n")

        #    cap = capidRotating(parsed_info_list)
        #    if not cap[0]:
        #        print "Capid problem, check logs"
        #        f.write(cap[1]+"\n")
                    #emailbody += "Capid problems for Crate {0}, RM {1}, QIE card {2}\n".format(crate, slot, card)
        #    f.write("\n")

        #f.close()
        #if emailbody != "":
                #monitor_teststand.send_email(subject="Capid error for teststand {0}".format(tstype), body=emailbody)
         #   pass
#            print "Waiting {0} minutes till the next check".format(options.sleep)
#            sleep(60*options.sleep)
    except KeyboardInterrupt:
        print "bye!"
        sys.exit()
    except Exception as ex:
        print ex


    
    

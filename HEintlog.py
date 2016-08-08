####################################################################
# Type: SCRIPT                                                     #
#                                                                  #
# Description: This script logs all BRIDGE, IGLOO2, and nGCCM      #
# registers as well as the power supply and time. This script is   #
# to run continuously, logging at a user set period.               #
####################################################################

from hcal_teststand import *
from hcal_teststand.hcal_teststand import teststand
from hcal_teststand.utilities import *
import sys
import os
from iglooSpyHE import *
from optparse import OptionParser
from time import sleep,strftime
import numpy
from commands import getoutput
from sqlite3 import *
# CLASSES:
# /CLASSES

# FUNCTIONS:
def log_link(ts,erro):
	log = "%% LINK\n"
	err=''
	uips=ts.uhtr_ips
	for cs in uips:
		raw=uhtr.get_raw_status(ip=uips[cs]).values()[0].split('\n')
		links=[]
		baddata=[]
		rollc=[]
		for l in raw:
			if 'BadCounter' in l: links.extend(l.split('BadCounter')[-1].split())
			if 'Bad Data' in l: baddata.extend(l.split('Bad Data')[-1].split())
			if 'Rollover Count' in l: rollc.extend(l.split('Rollover Count')[-1].split())
		if links != ['ON']*24: err+='link status: {0} for BE{1}\n'.format(links,cs)
#		if baddata != ['0']*24: err+='Bad data: {0} for BE{1}\n'.format(baddata,cs)
		log+='link status: {0} for BE{1}\n'.format(links,cs)
		log+='Bad data: {0} for BE{1}\n'.format(baddata,cs)
		log+='Rollover Count: {0} for BE{1}\n'.format(rollc,cs)
#	if err: erro['link']=err
	return log
		
def log_igloo(ts):
	log=''
	error=''
	crate_slot_card=[[4,4,1],[4,4,2]]
	for csc in crate_slot_card:
		iglooinfo=getInfoFromSpy_per_card(4342,csc[0],csc[1],csc[2],Nsamples=5)
		for nspy in iglooinfo:
			log+='\ncrate{0} slot{1} card{2} {3}\n'.format(csc[0],csc[1],csc[2],nspy)
			for nqie in iglooinfo[nspy]:
				log+='\t{0}: {1}\n'.format(nqie,iglooinfo[nspy][nqie])
	log="%% IGLOOSPY\n"+log
	return log

def log_registers(ts):		# Scale 0 is the sparse set of registers, 1 is full.
	log=''
	log += "%% REGISTERS\n"
	cmds=[]
	cmds.extend( [
			'get fec1-LHC_clk_freq' # put your registers to logger here
			])
	output = ngfec.send_commands(ts=ts, cmds=cmds)
	for result in output:
		log += "{0} -> {1}\n".format(result["cmd"], result["result"])
	return log
	
def record(ts=False,c=False,path="data/unsorted", scale=0):
	log = ""
	err={}
	t_string = time_string()[:-4]
	t0 = time_string()

	# Log registers:
	log += log_registers(ts=ts)
	log += "\n"
	
	# Log link:
	#log += log_link(ts,err)
	#log += "\n"

	# Log igloo:
	log += log_igloo(ts)
	log += "\n"
	
	# Log other:
#	log += "[!!]%% WHAT?\n(There is an error counter, which I believe is in the I2C register. This only counts GBT errors from GLIB to ngCCM. I doubt that Ozgur has updated the GLIB v3 to also count errors from ngCCM to GLIB. That would be useful to have if the counter exists.\nI also want to add, if there is time, an error counter of TMR errors. For the DFN macro TMR code, I implement an error output that goes high if all three outputs are not the same value. This would monitor only a couple of D F/Fs but I think it would be useful to see if any TMR errors are detected.)\n\n"

	# Time:
	t1 = time_string()
	log = "%% TIMES\n{0}\n{1}\n\n".format(t0, t1) + log
	isreg=[line for line in log.split('%% IGLOOSPY\n')[0].split('\n') if '->' in line]
	badrate=len([line for line in isreg if 'ERROR!!' in line])*100/len(isreg)
	if badrate>50:err['register']='logger cannot read registers, bad register rate: {0}%'.format(badrate)
	errs='\n'.join(err.values())
	if errs:	os.system("mail -s 'logger_information' yanchu@cern.ch <<EOF\nERROR in {0}.log:\n\n{1}\nEOF".format(t_string,errs))
	# Write log:
	path += "/{0}".format(t_string[:-7])
	scale_string = ""
	if scale == 0:
		scale_string = "sparse"
	elif scale == 1:
		scale_string = "full"
	print ">> {0}: Created a {1} log file named \"{2}.log\" in directory \"{3}\"".format(t1[:-4], scale_string, t_string, path)
	if not os.path.exists(path):
		os.makedirs(path)
	with open("{0}/{1}.log".format(path, t_string), "w") as out:
		out.write(log.strip())
	if c: conn.commit()
	return log
# /FUNCTIONS

# MAIN:
if __name__ == "__main__":
	# Script arguments:
	parser = OptionParser()
	parser.add_option("-t", "--teststand", dest="ts",
		default="HEint28",
		help="The name of the teststand you want to use (default is \"HEint28\"). Unless you specify the path, the directory will be put in \"data\".",
		metavar="STR"
	)
	parser.add_option("-o", "--fileName", dest="out",
		default="",
		help="The name of the directory you want to output the logs to (default is \"ts_904\").",
		metavar="STR"
	)
	parser.add_option("-s", "--sparse", dest="spar",
		default=10,
		help="The sparse logging period in minutes (default is 10).",
		metavar="FLOAT"
	)
	parser.add_option("-f", "--full", dest="full",
		default=0,
		help="The bkp_reset period in days (default is 0).",
		metavar="FLOAT"
	)
	parser.add_option("-T", "--time", dest="ptime",
		default='',
		help="The full logging time in a day (default is empty).",
		metavar="STR"
	)
	parser.add_option("-D", "--dd", dest="db",
			  default=True, action='store_false',
			  help='disable database.'
			  )
	(options, args) = parser.parse_args()
	name = options.ts
	period = float(options.spar)
	if not options.out:
		path = "data/ts_{0}".format(name)
	elif "/" in options.out:
		path = options.out
	else:
		path = "data/" + options.out
	c=False
	if options.db:
		os.system('mkdir -p '+path)
		conn=connect(path+'/logger.db')
		c=conn.cursor()

	period_long = float(options.full)
	
	# Set up teststand:
	ts = teststand(name)
	
	# Print information:
	print ">> The output directory is {0}.".format(path)
	print ">> The logging period is {0} minutes.".format(period)
	print ">> (A BackPlane reset signal will be sent every {0} days.)".format(period_long)
	if c: print ">> Writing to database {0}/logger.db.".format(path)
	# Logging loop:
	z = True
	t0 = 0
	t0_long = 0
	while z == True:
		dt = time.time() - t0
		dt_long = time.time() - t0_long
		if (period_long!=0) and (dt_long > period_long*86400):
			t0_long = time.time()
			bkp_reset(ts)
		if (period!=0) and (dt > period*60):
			t0 = time.time()
			record(ts=ts,c=c, path=path, scale=0)
		if strftime("%H:%M") == options.ptime:
			record(ts=ts,c=c, path=path, scale=1)
		else:
			sleep(1)
#		z = False
	
# /MAIN

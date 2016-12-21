##############################################
# at_reg.py -
#    A script to test the registers of a QIE card.
#
# Author: O. Kamer Koseyan - Novemer 11 - 12, 2015
##############################################

import sys
from random import randint
from hcal_teststand import *
from hcal_teststand.utilities import logger
from hcal_teststand.hcal_teststand import teststand
from ROOT import *

at = tests.acceptance(name="reg")
v = at.verbose
ts = at.ts			# Create teststand object for ngfec.send_commands()
registers = []			# List of commands to be sent to ngFEC tool
names = []			# List of names ordered as in registers list.
fe_RBX = at.fe_RBX
port= at.ng_port
fe_crate = at.fe_crate
fe_slot = at.fe_slot
n = at.n
numdic = {}
errdic = {}

def rand(size = 1):
	output = ''

	if size % 32:
		output += hex(randint(0, 2**(size % 32-1))) + ' '
	for i in range(int(size/32)):
		output += hex(randint(0, 2**32-1)) + ' '

	return output[:-1]

def register(name = None, size = 1, n = 5):
	cmds = []
	for i in range(n):
		r = rand(size)
		cmds += ['put {0} {1}'.format(name, r), 'get {0}'.format(name)]
	return cmds

def create_plots(at = None, names = None, dic = None, k = 1):
	gROOT.SetStyle("Plain")
	gStyle.SetOptStat(0)
	at.canvas.Divide(1, k)
	tothist = []
	rwhist = []
	xhist = []
	stacks = []
	for i in range(k):
		namespart = names[i*len(names)/k: (i+1)*len(names)/k]	# On (i+1)*len(names)/n, first i*len(names) is done, then the division by n. By that way, i = k - 1 => (i+1)*len(names)/k = len(names). So we don't lose any bins because of integer division.
		tothist.append(TH1F("Total_{0}".format(i+1), "", len(namespart), -0.5, len(namespart)-0.5))
		rwhist.append(TH1F("R/W_{0}".format(i+1), "", len(namespart), -0.5, len(namespart)-0.5))
		xhist.append(TH1F("Exec_{0}".format(i+1), "", len(namespart), -0.5, len(namespart)-0.5))
		stacks.append(THStack("Error_{0}".format(i+1), ""))
		tothist[i].SetFillColor(kGreen)
		rwhist[i].SetFillColor(kRed)
		xhist[i].SetFillColor(kOrange)
		for j, name in enumerate(namespart):
			tothist[i].GetXaxis().SetBinLabel(j+1, name)
			rwhist[i].GetXaxis().SetBinLabel(j+1, name)
			xhist[i].GetXaxis().SetBinLabel(j+1, name)
			tothist[i].Fill(j, dic[name][1][0])
			rwhist[i].Fill(j, dic[name][1][1])
			xhist[i].Fill(j, dic[name][1][2])
		tothist[i].GetXaxis().LabelsOption("vd")
		rwhist[i].GetXaxis().LabelsOption("vd")
		xhist[i].GetXaxis().LabelsOption("vd")
		at.canvas.cd(i + 1)
#		gPad.SetBottomMargin(-10)
#		gPad.SetLogy(1)
		tothist[i].GetXaxis().SetLabelOffset(0.02)
		tothist[i].Write()
		rwhist[i].Write()
		xhist[i].Write()
		stacks[i].Add(rwhist[i])
		stacks[i].Add(xhist[i])
		stacks[i].Write()
		tothist[i].SetMaximum(1.15*n)
		tothist[i].SetMinimum(0)
		stacks[i].SetMaximum(1.15*n)
		stacks[i].SetMinimum(0)
		tothist[i].Draw()
		stacks[i].Draw("SAME")
	at.write()
#	return 0

def main():
	at.start(nouid=True)
	print

	for i_qie in range(1, 13):
		registers.extend(
			register("HE{0}-{1}-{2}-QIE{3}_Lvds".format(fe_RBX, fe_crate, fe_slot, i_qie), 1, n) +			# 1 bit
			register("HE{0}-{1}-{2}-QIE{3}_Trim".format(fe_RBX, fe_crate, fe_slot, i_qie), 2, n) +			# 2 bits
			register("HE{0}-{1}-{2}-QIE{3}_DiscOn".format(fe_RBX, fe_crate, fe_slot, i_qie), 1, n) +			# 1 bit
			register("HE{0}-{1}-{2}-QIE{3}_TGain".format(fe_RBX, fe_crate, fe_slot, i_qie), 1, n) +			# 1 bit
			register("HE{0}-{1}-{2}-QIE{3}_TimingThresholdDAC".format(fe_RBX, fe_crate, fe_slot, i_qie), 8, n) +	# 8 bits
			register("HE{0}-{1}-{2}-QIE{3}_TimingIref".format(fe_RBX, fe_crate, fe_slot, i_qie), 3, n) +		# 3 bits
			register("HE{0}-{1}-{2}-QIE{3}_PedestalDAC".format(fe_RBX, fe_crate, fe_slot, i_qie), 6, n) +		# 6 bits
			register("HE{0}-{1}-{2}-QIE{3}_CapID0pedestal".format(fe_RBX, fe_crate, fe_slot, i_qie), 4, n) +		# 4 bits
			register("HE{0}-{1}-{2}-QIE{3}_CapID1pedestal".format(fe_RBX, fe_crate, fe_slot, i_qie), 4, n) +		# 4 bits
			register("HE{0}-{1}-{2}-QIE{3}_CapID2pedestal".format(fe_RBX, fe_crate, fe_slot, i_qie), 4, n) +		# 4 bits
			register("HE{0}-{1}-{2}-QIE{3}_CapID3pedestal".format(fe_RBX, fe_crate, fe_slot, i_qie), 4, n) +		# 4 bits
			register("HE{0}-{1}-{2}-QIE{3}_FixRange".format(fe_RBX, fe_crate, fe_slot, i_qie), 1, n) +			# 1 bit
			register("HE{0}-{1}-{2}-QIE{3}_RangeSet".format(fe_RBX, fe_crate, fe_slot, i_qie), 2, n) +			# 2 bits
			register("HE{0}-{1}-{2}-QIE{3}_ChargeInjectDAC".format(fe_RBX, fe_crate, fe_slot, i_qie), 3, n) +		# 3 bits
			register("HE{0}-{1}-{2}-QIE{3}_RinSel".format(fe_RBX, fe_crate, fe_slot, i_qie), 4, n) +			# 4 bits
			register("HE{0}-{1}-{2}-QIE{3}_Idcset".format(fe_RBX, fe_crate, fe_slot, i_qie), 5, n) +			# 5 bits
			register("HE{0}-{1}-{2}-QIE{3}_CalMode".format(fe_RBX, fe_crate, fe_slot, i_qie), 1, n) +			# 1 bit
			register("HE{0}-{1}-{2}-QIE{3}_CkOutEn".format(fe_RBX, fe_crate, fe_slot, i_qie), 1, n) +			# 1 bit
			register("HE{0}-{1}-{2}-QIE{3}_TDCMode".format(fe_RBX, fe_crate, fe_slot, i_qie), 1, n) +			# 1 bit
			register("HE{0}-{1}-{2}-Qie{3}_ck_ph".format(fe_RBX, fe_crate, fe_slot, i_qie), 4, n)			# 4 bits
		)

	registers.extend(
		### Top:
		register("HE{0}-{1}-{2}-iTop_CntrReg_CImode".format(fe_RBX, fe_crate, fe_slot), 1, n) +			# 1 bit
		register("HE{0}-{1}-{2}-iTop_CntrReg_InternalQIER".format(fe_RBX, fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HE{0}-{1}-{2}-iTop_CntrReg_OrbHistoClear".format(fe_RBX, fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HE{0}-{1}-{2}-iTop_CntrReg_OrbHistoRun".format(fe_RBX, fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HE{0}-{1}-{2}-iTop_CntrReg_WrEn_InputSpy".format(fe_RBX, fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HE{0}-{1}-{2}-iTop_AddrToSERDES".format(fe_RBX, fe_crate, fe_slot), 16, n) +			# 16 bits
		register("HE{0}-{1}-{2}-iTop_CtrlToSERDES_i2c_go".format(fe_RBX, fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HE{0}-{1}-{2}-iTop_CtrlToSERDES_i2c_write".format(fe_RBX, fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HE{0}-{1}-{2}-iTop_DataToSERDES".format(fe_RBX, fe_crate, fe_slot), 32, n) +			# 32 bits
		register("HE{0}-{1}-{2}-iTop_LinkTestMode".format(fe_RBX, fe_crate, fe_slot), 8, n) +			# 8 bits
		register("HE{0}-{1}-{2}-iTop_LinkTestPattern".format(fe_RBX, fe_crate, fe_slot), 32, n) +			# 32 bits
		register("HE{0}-{1}-{2}-iTop_scratch".format(fe_RBX, fe_crate, fe_slot), 32, n) +				# 32 bits
		register("HE{0}-{1}-{2}-iTop_UniqueID".format(fe_RBX, fe_crate, fe_slot), 64, n) +				# 64 bits
		### Bottom:
		register("HE{0}-{1}-{2}-iBot_CntrReg_CImode".format(fe_RBX, fe_crate, fe_slot), 1, n) +			# 1 bit
		register("HE{0}-{1}-{2}-iBot_CntrReg_InternalQIER".format(fe_RBX, fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HE{0}-{1}-{2}-iBot_CntrReg_OrbHistoClear".format(fe_RBX, fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HE{0}-{1}-{2}-iBot_CntrReg_OrbHistoRun".format(fe_RBX, fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HE{0}-{1}-{2}-iBot_CntrReg_WrEn_InputSpy".format(fe_RBX, fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HE{0}-{1}-{2}-iBot_AddrToSERDES".format(fe_RBX, fe_crate, fe_slot), 16, n) +			# 16 bits
		register("HE{0}-{1}-{2}-iBot_CtrlToSERDES_i2c_go".format(fe_RBX, fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HE{0}-{1}-{2}-iBot_CtrlToSERDES_i2c_write".format(fe_RBX, fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HE{0}-{1}-{2}-iBot_DataToSERDES".format(fe_RBX, fe_crate, fe_slot), 32, n) +			# 32 bits
		register("HE{0}-{1}-{2}-iBot_LinkTestMode".format(fe_RBX, fe_crate, fe_slot), 8, n) +			# 8 bits
		register("HE{0}-{1}-{2}-iBot_LinkTestPattern".format(fe_RBX, fe_crate, fe_slot), 32, n) +			# 32 bits
		register("HE{0}-{1}-{2}-iBot_scratch".format(fe_RBX, fe_crate, fe_slot), 32, n) +				# 32 bits
		register("HE{0}-{1}-{2}-iBot_UniqueID".format(fe_RBX, fe_crate, fe_slot), 64, n)				# 64 bits
		)

	for reg in registers[1::2*n]:
		names.extend([reg[4:]])

	output = ngfec.send_commands(ts,port=port, cmds = registers, script = False, progbar = True)

	errlist = []
	totaltests = 0
	rwerr = 0
	xerr = 0
	for i, (put, get) in enumerate(zip(output[::2], output[1::2])):
#		if ' '.join(put['cmd'].split()[2:]).replace('0x', '') == get['result'].replace('0x', ''):
		totaltests += 1
		if 'ERROR' in put['result'] or 'ERROR' in get['result']:
			xerr += 1
		elif ' '.join(put['cmd'].split()[2:]).replace('0x', '') != get['result'].replace('0x', ''):
			rwerr += 1
			errlist.append([' '.join(put['cmd'].split()[2:]).replace('0x', ''), get['result'].replace('0x', '')])
		if 'ERROR' in put['result']:
			errlist.append([put['cmd'], put['result']])
		if 'ERROR' in get['result']:
			errlist.append([get['cmd'], get['result']])
		if not (i+1) % n:
			errdic.update({get['cmd'][4:]: [errlist, [totaltests, rwerr, xerr]]})
			errlist = []
			totaltests = 0
			rwerr = 0
			xerr = 0

#---------------Last report of errors------------------
	print "\n====== SUMMARY ============================"
	if errdic.values().count([[], [n, 0, 0]]) == len(names):
		print '[OK] There were no errors.'
	else:
		print 'R/W errors (put != get):'
		for name in names:
			for error in errdic[name][0]:
				if (error[0] != error[1] and not 'ERROR' in error[1]):
					print '\t*Register: ' + name + ' -> Data: 0x' + error[0].replace(' ', ' 0x') + ' != 0x' + error[1].replace(' ', ' 0x')

		print '\nExecution errors:'
		for name in names:
			for error in errdic[name][0]:
				if 'ERROR' in error[1]:
					print '\t*Command: ' + error[0] + ' -> Result: ' + error[1]
	print "\n===========================================\n"

#---------------Create histogram-----------------------
	create_plots(at, names, errdic, 8)

	if v:
		for put, get in zip(output[::2], output[1::2]):
			if ' '.join(put['cmd'].split()[2:]).replace('0x', '') == get['result'].replace('0x', '') and not 'ERROR' in put['result']:
				at.silentlog('[OK] :: {0} -> {1} == {2} -> {3}\n'.format(put['cmd'], put['result'], get['cmd'], '0x' + get['result'].replace('0x', '').replace(' ', ' 0x')))
			elif 'ERROR' in get['result']:
				at.silentlog('[!!] :: {0} -> {1} != {2} -> {3}\n'.format(put['cmd'], put['result'], get['cmd'], get['result']))
			elif ' '.join(put['cmd'].split()[2:]).replace('0x', '') == get['result'].replace('0x', '') and 'ERROR' in put['result']:
				at.silentlog('[!!] :: {0} -> {1} == {2} -> {3}\n'.format(put['cmd'], put['result'], get['cmd'], '0x' + get['result'].replace('0x', '').replace(' ', ' 0x')))
			else:
				at.silentlog('[!!] :: {0} -> {1} != {2} -> {3}\n'.format(put['cmd'], put['result'], get['cmd'], '0x' + get['result'].replace('0x', '').replace(' ', ' 0x')))
		print '\nPrinting raw comparisons into file: [OK]'
	else:
		print
if __name__ == "__main__":
	main()

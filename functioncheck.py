#!/usr/bin/env python3
import subprocess as sub
import sys 
import re
import os.path, time
import psutil

### Config
DISK_USAGE_THRESHOLD = 75
LVMVG_USAGE_THRESHOLD = .75
MEM_USED_THRESHOLD = .75
BACKUP_HOURS_THRESHOLD = 48

### TOOLS

def printf(format, *args):
    sys.stdout.write(format % args)

def call(cmd):
    p = sub.Popen(cmd.split(),stdout=sub.PIPE,stderr=sub.PIPE)
    p.wait()
    (out, err) = p.communicate()
    if len(err)>0:
        print(err)
        sys.exit(1)
    return out.decode("utf-8")

def grep(lines, string):
	out = ''
	for line in lines.split('\n'): 
		if re.search(string, line):
			out += line + '\n'
	return out

def ungrep(lines, string):
	out = ''
	for line in lines.split('\n'): 
		if not re.search(string, line):
			out += line + '\n'
	return out

### PRINT

def printRaidState():
	mdstat = call('cat /proc/mdstat').split('\n')
	mdstat = mdstat[1:-2]
	hddsUp = mdstat[1].split(' ')[-1]
	if not hddsUp == "[UU]" and not hddsUp == "[UUU]":
		print("RAID: degraded.")
		for line in mdstat:
			print(line)

def printRsnapshotState(dir):
	dir += 'alpha.0'
	backupTime = os.path.getctime(dir)
	backupAge = time.time() - backupTime
	backupAge /= 3600
	if backupAge > BACKUP_HOURS_THRESHOLD: 
		print("Most recent backup is too old: %s" % time.ctime(os.path.getctime(dir)))
	print("INFO: Backup size: %s" % call('du -sh ' + dir))

def printProcessStatus(processes):
	for process in processes:
		if not testProcessRunning(process):
			print(process + " is NOT running.")
		
def printDf(hdds):
	for hdd in hdds.split('\n'):
		if(len(hdd)>0):
			printDfLine(hdd)

def printDfLine(line):
	if not len(line.split()) == 6: return
	(dev,size,used,free,ratio,mount) = line.split()
	if int(ratio.replace("%","")) > DISK_USAGE_THRESHOLD:
		printf("%15s:\t\t%5s (%5s size, %5s used, %5s free)\n",dev,ratio,size,used,free)
		

def printUptime():
	line = call('uptime')
	uptime = line.split(',')[0].split('up')
	print("Up since %s (uptime: %s)" % (uptime[0].strip(), uptime[1].strip()))
	
def printMemoryStatus():
	free = call('free -m').split('\n')
	line = free[1].split()
	val = int(line[2][:-1])-int(line[6][:-1])
	maxMem = int(line[1][:-1])
	if(val/maxMem > MEM_USED_THRESHOLD):
		print("High memory usage: %d%s MiB of %s MiB are used." % (val,line[2][-1:],line[1]))
	#else:
	##	print("Memory ok %f" % (val/maxMem))

def printLVMVGStatus():
	#TODO: currently only supports one line, i.e. one vg
	status = call('vgdisplay -s').split()
	total = "%s %s" % (status[1],status[2])
	used = "%s %s" % (status[3][1:],status[4])
	free = "%s %s" % (status[7],status[8])
	ratiofree = float(status[3][1:]) / float(status[1])
	vgname = status[0]
	if LVMVG_USAGE_THRESHOLD < ratiofree:
		print("LVM VG %s free %.2f %% WARN (threshold %.0f %%) " % (vgname, ratiofree*100, LVMVG_USAGE_THRESHOLD*100))	
	#else:
	#	print("LVM VG %s free %.2f %% OK (threshold %.0f %%) " % (vgname, ratiofree*100, LVMVG_USAGE_THRESHOLD*100))	

def printDivider():
	print()	

def printHeader(string):
	printDivider()
	print("### " + string)

def printSubsection(string):
	printDivider()
	print("# " + string)

### TEST

def testProcessRunning(process):
	#return len(grep(call('ps aux'),process).split('\n'))-1 >= 1
	process = process[1:15]
	return len(call('pgrep -f ' + process)) >= 1

def checkMetadataProxies():
	netns_call = call('ip netns')
	netns = []
	for ns in netns_call.split("\n"):
		if ns.startswith("qrouter"):
			nsid = ns[8:]
			netns.append(nsid)
	count = 0
	for pid in psutil.pids():
		p = psutil.Process(pid)
		cmdline = p.cmdline()
		if any("metadata-proxy" in s for s in cmdline):
			routerid = cmdline[4][12:]
			if not any(routerid in t for t in netns):
				print("No metadata-proxy found for router with ID: %s" % routerid)

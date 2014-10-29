#!/usr/bin/env python3
import subprocess as sub
import sys 
import re
import os.path, time

### Config
DISK_USAGE_THRESHOLD = 75
BACKUP_HOURS_THRESHOLD = 24

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
	if not hddsUp == "[UU]":
		print("RAID: degraded.")
		for line in mdstat:
			print(line)

def printRsnapshotState(dir):
	dir += 'daily.0'
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
	return len(grep(call('ps aux'),process).split('\n'))-1 >= 1

### MAIN

def examples():
	printHeader("<hostname> Systemreport")

	hdds = ungrep(call('df -h'),'tmpfs')
	printDf(hdds)
	
	printProcessStatus(["processname", "processname", "processname"])
	
	printRsnapshotState('/var/rsnapshot/')
	
	printRaidState()

examples()

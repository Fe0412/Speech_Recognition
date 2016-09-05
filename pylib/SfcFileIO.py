#!/usr/bin/env /lang/y2k/exec/python


import os, sys
sys.path.insert(0, "/speech6/lang/y2k/pylib")
from SfcPwd import *


def IsOpenReadG(szFile):
	if szFile == "-" or szFile == "<stdin>": return sys.stdin
	ichPipe = szFile.rfind("|")
	if (ichPipe > 0) and ((ichPipe + 1 == len(szFile)) or \
		szFile[ichPipe+1:].isspace()) and not szFile[:ichPipe].isspace():
		return os.popen(szFile[:ichPipe])
	if (szFile[-3:] == ".gz") or (szFile[-2:] == ".Z"):
		return os.popen("gzip -cd " + szFile)
	if szFile[-4:] == ".bz2":
		return os.popen("bzip2 -cd " + szFile)
	return open(szFile)

def OsOpenWriteG(szFile):
	if szFile == "-" or szFile == "<stdout>": return sys.stdout
	if szFile == "<stderr>": return sys.stderr
	ichPipe = szFile.find("|")
	if (ichPipe >= 0) and (not ichPipe or szFile[:ichPipe].isspace()) and \
		(ichPipe + 1 < len(szFile)) and not szFile[ichPipe+1:].isspace():
		return os.popen(szFile[ichPipe+1:], "w")
	if (szFile[-3:] == ".gz"):
		return os.popen("gzip > " + szFile, "w")
	if szFile[-4:] == ".bz2":
		return os.popen("bzip2 > " + szFile, "w")
	return open(szFile, "w")

def SzNormFileNameReadG(szFile, szRef):
	if not szFile or szFile == "-" or szFile.startswith("<") or \
		szFile.find("|") >= 0:
		return szFile
	if szFile[:1] == "/" or szRef == "/dev/null":
		return szFile
	return os.path.join(os.path.dirname(szRef), szFile)

def SzNormFileNameWriteG(szFile, szRef):
	if not szFile or szFile == "-" or szFile.startswith("<") or \
		szFile.find("|") >= 0:
		return szFile
	if szFile[:1] == "/" or szRef == "/dev/null":
		return szFile
	if szRef[:1] == "/":
		return SzAbsPathNameG(szFile)

	rgszFile = szFile.split("/")
	rgszRef = szRef.split("/")
	cszMatch = 0
	cszFile = len(rgszFile) - 1
	cszRef = len(rgszRef) - 1
	while cszMatch < cszFile and cszMatch < cszRef:
		if rgszFile[:cszMatch+1] != rgszRef[:cszMatch+1]: break
		cszMatch += 1
	if cszRef - cszMatch > 3: return SzAbsPathNameG(szFile)
	for cszCheck in xrange(cszMatch + 1, cszRef + 1):
		if os.path.islink("/".join(rgszRef[:cszCheck])):
			return SzAbsPathNameG(szFile)
	return "../" * (cszRef - cszMatch) + "/".join(rgszFile[cszMatch:])

def SzNormFileNameReadWriteG(szName, szBase, fWrite = False):
	if fWrite: return SzNormFileNameWriteG(szName, szBase)
	else: return SzNormFileNameReadG(szName, szBase)



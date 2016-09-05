#!/usr/bin/env /lang/y2k/exec/python


import os, re, sys


class ObjType:
	def __init__(self, szName):
		self.szNameM = szName
		self.szDocM = None
		self.rgszParentM = None
		self.rgfFeatM = {}
		self.rgtpOpM = []


class ObjTypeColl:
	fWarnDefaultM = False

	def __init__(self):
		self.rgotM = {}
		self.rgszTypeOrderM = []

	def ReadFile(self, szFile):
		rgfOld = {}
		for szObjType in self.rgotM.keys(): rgfOld[szObjType] = True
		isIn = open(szFile)
		while True:
			szLine = isIn.readline()
			if not szLine: break
			if szLine[-1:] == "\n": szLine = szLine[:-1]
			while szLine[-1:] == "\\":
				szLine = szLine[:-1]
				szCont = isIn.readline()
				if not szCont: break
				if szCont[-1:] == "\n": szCont = szCont[:-1]
				szLine += szCont
			szLine = re.sub(r"-=", " -= ", szLine)
			szLine = re.sub(r"\+=", " += ", szLine)
			rgszLine = szLine.split()
			if not rgszLine or rgszLine[0][0] == "#": continue
			rgszType = rgszLine[0].split(".")
			szObjType = rgszType[0]
			if rgfOld.has_key(szObjType):
				print >>sys.stderr, "***Warning***: overriding previous " + \
					"definition (%s): %s" % (szFile, szObjType)
				del rgfOld[szObjType]
				del self.rgotM[szObjType]
				self.rgszTypeOrderM.remove(szObjType)
			if not self.rgotM.has_key(szObjType):
				self.rgotM[szObjType] = ObjType(szObjType)
				self.rgszTypeOrderM.append(szObjType)
			ot = self.rgotM[szObjType]
			if len(rgszType) == 2 and rgszType[1] == "doc":
				if ot.szDocM != None: raise IOError, \
					"Specified property twice (%s): %s" % (szFile, szLine)
				ot.szDocM = " ".join(rgszLine[1:])
				continue
			if len(rgszType) == 2 and rgszType[1] == "parents":
				if ot.rgszParentM != None: raise IOError, \
					"Specified property twice (%s): %s" % (szFile, szLine)
				ot.rgszParentM = rgszLine[1:]
				for szParent in ot.rgszParentM:
					if szParent == szObjType or \
						not self.rgotM.has_key(szParent): raise IOError, \
						"Invalid parent (%s): %s" % (szFile, szLine)
				continue
			if len(rgszType) == 2:
				rgszType.append("default")
				if not ObjTypeColl.fWarnDefaultM:
					ObjTypeColl.fWarnDefaultM = True
					print >>sys.stderr, "*warning*: should add '.default' " + \
						"to end of first field (%s): %s" % (szFile, szLine)
			if len(rgszType) != 3: raise IOError, \
				"Invalid first field (%s): %s" % (szFile, szLine)
			(szFeat, szSpec) = rgszType[1:]
			ot.rgfFeatM[szFeat] = True
			wOp = 0
			rgszVal = rgszLine[1:]
			if rgszVal and rgszVal[0] == "+=":
				wOp = 1; rgszVal.pop(0)
			elif rgszVal and rgszVal[0] == "-=":
				wOp = -1; rgszVal.pop(0)
			ot.rgtpOpM.append((szFeat, szSpec, wOp, rgszVal))
		isIn.close()

	def RgszGetValsSubR(self, szObjType, rgfFeat):
		if not self.rgotM.has_key(szObjType): raise ValueError, \
			"Invalid object type: " + szObjType
		ot = self.rgotM[szObjType]
		rgszColl = {}
		if ot.rgszParentM != None:
			for szParent in ot.rgszParentM:
				rgszParent = self.RgszGetValsSubR(szParent, rgfFeat)
				for tpKey in rgszParent.keys():
					if not rgszColl.has_key(tpKey): rgszColl[tpKey] = ""
					rgszColl[tpKey] = " ".join(rgszColl[tpKey].split() + \
						rgszParent[tpKey].split())
		for tpOp in ot.rgtpOpM:
			tpKey = tpOp[0:2]
			(wOp, rgszVal) = tpOp[2:4]
			if wOp == 0: rgszColl[tpKey] = " ".join(rgszVal)
			else:
				if not rgszColl.has_key(tpKey): rgszColl[tpKey] = ""
				rgszOld = rgszColl[tpKey].split()
				if wOp == 1: rgszColl[tpKey] = " ".join(rgszOld + rgszVal)
				else:
					try:
						for szDel in rgszVal:
							rgszOld.remove(szDel)
					except ValueError:
						raise ValueError, "Invalid subtraction: %s.%s.%s" % \
							(ot.szNameM, tpKey[0], tpKey[1])
					rgszColl[tpKey] = " ".join(rgszOld)
		for szFeat in ot.rgfFeatM.keys(): rgfFeat[szFeat] = True
		return rgszColl

	def RgszGetValsR(self, szObjType, szHostType):
		rgfFeat = {}
		rgszColl = self.RgszGetValsSubR(szObjType, rgfFeat)
		rgszRet = {}
		for szFeat in rgfFeat.keys():
			rgszCur = []
			if rgszColl.has_key((szFeat, "all")):
				rgszCur += rgszColl[(szFeat, "all")].split()
			if rgszColl.has_key((szFeat, szHostType)):
				rgszCur += rgszColl[(szFeat, szHostType)].split()
			elif rgszColl.has_key((szFeat, "default")):
				rgszCur += rgszColl[(szFeat, "default")].split()

			rgszDel = []
			if rgszColl.has_key((szFeat, "-all")):
				rgszDel += rgszColl[(szFeat, "-all")].split()
			if rgszColl.has_key((szFeat, "-" + szHostType)):
				rgszDel += rgszColl[(szFeat, "-" + szHostType)].split()
			elif rgszColl.has_key((szFeat, "-default")):
				rgszDel += rgszColl[(szFeat, "-default")].split()
			try:
				for szDel in rgszDel:
					rgszCur.remove(szDel)
			except ValueError:
				raise ValueError, "Invalid subtraction: %s.%s.*" % \
					(szObjType, szFeat)
			rgszRet[szFeat] = " ".join(rgszCur)
		return rgszRet

	def LoadDefaultFiles(self):
		if os.environ.has_key("SMK_OBJTYPE_FILE"):
			for szFile in os.environ["SMK_OBJTYPE_FILE"].split(":"):
				if szFile and os.path.exists(szFile):
					self.ReadFile(szFile)
		szLocalTypeFile = os.path.expanduser("~/.Mk.objtypes")
		if os.path.exists(szLocalTypeFile): self.ReadFile(szLocalTypeFile)


def SzReadDefaultObjTypeFileG(szFile, szDefault):
	szRet = None
	if os.path.exists(szFile):
		isIn = open(szFile)
		for szLine in isIn.xreadlines():
			rgsz = szLine.split()
			if not rgsz or rgsz[0][0] == "#": continue
			if len(rgsz) > 1 or szRet:
				sys.exit("Invalid default objtype file: " + szFile)
			szRet = rgsz[0]
		isIn.close()
	if not szRet: szRet = szDefault
	return szRet



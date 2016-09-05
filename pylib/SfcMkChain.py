#!/usr/bin/env /speech6/lang/y2k/exec/python
#
#	$Id: SfcMkChain.py,v 1.18 2003/10/23 00:56:27 stanchen Exp $
#


import os, re, stat, sys
sys.path.insert(0, "/speech6/lang/y2k/pylib")
from SfcFileIO import *
from SfcPwd import *


########################################################################
#	cluster entry
########################################################################
class ClustEnt:
	def __init__(self, szFeat, szVal, fExplicit):
		if not szVal: raise ValueError, "Empty directory name in chain."
		self.fReadOnlyM = (szVal[:1] == "-")
		if self.fReadOnlyM: szVal = szVal[1:]
		if szVal and szVal[-1] != "/": szVal += "/"
		self.szFeatM = szFeat
		self.szValM = szVal
		self.fExplicitM = fExplicit
		self.szReposHashM = None

	def OutputR(self, osOut, cchPrefix):
		szReadOnly = ""
		if self.fReadOnlyM: szReadOnly = "-"
		if not self.szValM:
			assert self.fReadOnlyM
			osOut.write("%s = %s" % (self.szFeatM, szReadOnly))
		elif cchPrefix and cchPrefix == len(self.szValM):
			osOut.write("%s = %s." % (self.szFeatM, szReadOnly))
		elif cchPrefix and self.szFeatM == self.szValM[cchPrefix:-1]:
			osOut.write("%s%s" % (szReadOnly, self.szFeatM))
		else:
			osOut.write("%s = %s%s" % \
				(self.szFeatM, szReadOnly, self.szValM[cchPrefix:-1]))


########################################################################
#	cluster in chain
########################################################################
class Cluster:
	def __init__(self):
		self.szNameM = None
		self.szBaseDirM = None
		self.fOverM = False
		self.rgceListM = []
		self.rgceHashM = {}

	def SetBaseDir(self, sz):
		if sz[:1] == "-": sz = sz[1:]
		if not sz: return
		if sz[-1] != "/": sz += "/"
		self.szBaseDirM = sz

	def SzCommonPrefixR(self):
		rg2szColl = []
		for ce in self.rgceListM:
			if ce.szValM: rg2szColl.append(ce.szValM[:-1].split("/"))
		if len(rg2szColl) < 2: return ""
		rgszFirst = rg2szColl[0]
		cszMin = len(rgszFirst)
		cszCommon = len(rgszFirst)
		for rgszCur in rg2szColl[1:]:
			if len(rgszCur) < cszMin: cszMin = len(rgszCur)
			while cszCommon > 0:
				if rgszCur[:cszCommon] == rgszFirst[:cszCommon]: break
				else: cszCommon -= 1
		if not cszCommon or (cszCommon == 1 and (not rgszFirst[0] or \
			rgszFirst[0] == ".")) or cszMin > cszCommon + 1: return ""
		return "/".join(rgszFirst[:cszCommon]) + "/"

	def OutputR(self, osOut):
		if self.szNameM: osOut.write("[%s] " % self.szNameM)
		osOut.write("(")
		szPrefix = self.SzCommonPrefixR()
		if szPrefix: osOut.write("BASE = %s, " % szPrefix[:-1])
		for ice in xrange(len(self.rgceListM)):
			if ice: osOut.write(", ")
			self.rgceListM[ice].OutputR(osOut, len(szPrefix))
		osOut.write(")")

	def SzOutputR(self):
		rgsz = []
		for ce in self.rgceListM:
			szReadOnly = ""
			if ce.fReadOnlyM: szReadOnly = "-"
			rgsz.append("%s = %s%s" % (ce.szFeatM, szReadOnly, ce.szValM[:-1]))
		szRet = "(" + ", ".join(rgsz) + ")"
		if self.szNameM: szRet = "[%s] " % self.szNameM + szRet
		return szRet

	def NewEntry(self, szFeat, szVal, fExplicit):
		self.FDeleteEntry(szFeat)
		szDir = szVal
		if szDir[:1] == "-": szDir = szDir[1:]
		if not szDir or fExplicit or os.path.isdir(szDir):
			ceNew = ClustEnt(szFeat, szVal, fExplicit)
			self.rgceListM.append(ceNew)
			self.rgceHashM[szFeat] = ceNew

	def FDeleteEntry(self, szFeat):
		if self.rgceHashM.has_key(szFeat):
			ceDel = self.rgceHashM[szFeat]
			self.rgceListM.remove(ceDel)
			del self.rgceHashM[szFeat]
			return True
		else: return False

	def ProcessEntry(self, rgszTok, rgszVar, cn, iclSrc):
		szErr = re.sub(r"['\"]", "", " ".join(rgszTok))
		if self.fOverM: raise IOError, \
			"OVER directive must be last entry in cluster: " + szErr

		if Chain.FGetTokenR(rgszTok, "'OVER"):
			if not rgszTok:
				iclLo = 1; iclHi = iclSrc
			else:
				szOp = rgszTok.pop(0)
				szVal = Chain.SzExpandFileNameR( \
					Chain.SzGetVarTokenR(rgszTok, szErr), rgszVar)
				iclFind = cn.IclFindR(szVal, iclSrc)
				if not iclFind:
					raise IOError, "Invalid cluster reference: " + szErr
				if szOp == "=" or szOp == "==":
					iclLo = iclFind; iclHi = iclFind
				elif szOp == "<":
					iclLo = 1; iclHi = iclFind - 1
				elif szOp == "<=":
					iclLo = 1; iclHi = iclFind
				elif szOp == ">":
					iclLo = iclFind + 1; iclHi = iclSrc
				elif szOp == ">=":
					iclLo = iclFind; iclHi = iclSrc
				else:
					raise IOError, "Illegal 'OVER' directive: " + szErr
			if iclLo < 1: iclLo = 1
			if iclHi >= iclSrc: iclHi = iclSrc - 1
			for iclLoop in xrange(iclLo, iclHi + 1):
				clCur = cn.rgclM[iclLoop]
				for ceOver in self.rgceListM:
					if ceOver.szValM:
						clCur.FDeleteEntry(ceOver.szFeatM)
						szCur = ceOver.szValM
						if ceOver.fReadOnlyM: szCur = "-" + szCur
						clCur.NewEntry(ceOver.szFeatM, szCur, \
							ceOver.fExplicitM)
					elif clCur.rgceHashM.has_key(ceOver.szFeatM):
						clCur.rgceHashM[ceOver.szFeatM].fReadOnlyM = \
							ceOver.fReadOnlyM
			self.fOverM = True
		elif len(rgszTok) >= 2 and re.match(r"'[A-Z0-9_]+$", rgszTok[0]) \
			and rgszTok[1] == "=":
			szFeat = Chain.SzGetVarTokenR(rgszTok, szErr)
			Chain.GetTokenR(rgszTok, "=", szErr)
			szVal = Chain.SzExpandFileNameR( \
				Chain.SzGetValTokenR(rgszTok, szErr), rgszVar)
			if szFeat == "BASE":
				szValNorm = SzNormFileNameReadG(szVal, cn.rgszFileM[-1])
				self.SetBaseDir(szValNorm)
			rgszVar[szFeat] = szVal
		elif len(rgszTok) >= 2 and rgszTok[0][0] == "'" and rgszTok[1] == "=":
			szFeat = Chain.SzGetVarTokenR(rgszTok, szErr)
			Chain.GetTokenR(rgszTok, "=", szErr)
			szVal = Chain.SzExpandFileNameR( \
				Chain.SzGetVarTokenR(rgszTok, szErr), rgszVar)
			if szVal == Chain.szNullEntryM:
				self.FDeleteEntry(szFeat)
			else:
				szVal = SzNormFileNameReadG(szVal, cn.rgszFileM[-1])
				self.NewEntry(szFeat, szVal, True)
		else:
			szFeat = Chain.SzGetVarTokenR(rgszTok, szErr)
			szPrefix = ""
			if szFeat[:1] == "-": szPrefix = "-"; szFeat = szFeat[1:]
			if not rgszVar.has_key("BASE"):
				raise IOError, "'BASE' var must be set: " + szErr
			szVal = szPrefix + os.path.join(rgszVar["BASE"], szFeat)
			self.NewEntry(szFeat, szVal, True)

	def ProcessCluster(self, rgszTok, cn, iclSrc):
		szErr = re.sub(r"['\"]", "", " ".join(rgszTok))
		if rgszTok and rgszTok[0] != "(":
			szDir = Chain.SzExpandFileNameR( \
				Chain.SzGetVarTokenR(rgszTok, szErr), cn.rgszVarM)
			szDir = SzNormFileNameReadG(szDir, cn.rgszFileM[-1])
			self.SetBaseDir(szDir)
			for szClust in Chain.rgszClustM:
				self.NewEntry(szClust, szDir, True)
		if Chain.FGetTokenR(rgszTok, "("):
			fFirst = True
			rgszVarT = cn.rgszVarM.copy()
			while True:
				rgszEnt = []
				while rgszTok and rgszTok[0] != "," and rgszTok[0] != ")":
					rgszEnt.append(rgszTok.pop(0))
				if not rgszTok:
					raise IOError, "Unexpected end of cluster: " + szErr

				if fFirst and len(rgszEnt) == 1 and \
					rgszEnt[0][0] == "'" and rgszEnt[0][1:] != "OVER":
					szDef = Chain.SzExpandFileNameR( \
						Chain.SzGetVarTokenR(rgszEnt, szErr), rgszVarT)
					szDef = SzNormFileNameReadG(szDef, cn.rgszFileM[-1])
					self.SetBaseDir(szDef)
					for szClust in Chain.rgszClustM:
						self.NewEntry(szClust, os.path.join(szDef, szClust),
							False)
				elif rgszEnt:
					self.ProcessEntry(rgszEnt, rgszVarT, cn, iclSrc)

				if rgszEnt: raise IOError, \
					"Unexpected tokens at end of entry: " + szErr
				szSep = rgszTok.pop(0)
				if szSep == ")": break
				fFirst = False


########################################################################
#	chain
########################################################################
class Chain:
	rgszClustM = [ "src", "inc", "obj", "bin", "exec", "doc", "data", "lib" ]
	szNullEntryM = "NULL"
	szChainPathVarM = "SMK_CHAIN_PATH"
	szChainCreateVarM = "SMK_CHAIN_CREATE"

	def SzExpandFileNameR(szSrc, rgszVar):
		szOrig = szSrc
		szPrefix = ""
		if szSrc[:1] == "-":
			szPrefix = szSrc[0]; szSrc = szSrc[1:]
		szSrc = os.path.expanduser(szSrc)
		rgszSav = os.environ
		os.environ = rgszVar
		szSrc = os.path.expandvars(szSrc)
		os.environ = rgszSav
		if szSrc.find("$") >= 0: raise ValueError, "Undefined var: " + szOrig
		return szPrefix + szSrc
	SzExpandFileNameR = staticmethod(SzExpandFileNameR)

	def __init__(self, szChain):
		self.rgclM = [ None ]
		self.rgszVarM = os.environ.copy()
		self.rgszFileM = []
		try:
			self.rgszFileM.append(".")
			self.ProcessChain(szChain)
			self.rgszFileM.pop()
			self.ExpandRepos()
		except:
			if not self.rgszFileM: szErrFile = "."
			else: szErrFile = self.rgszFileM[-1]
			print >>sys.stderr, "Error in file '%s' when processing chain: %s" \
				% (szErrFile, szChain)
			print >>sys.stderr, \
				"  %s: %s" % (str(sys.exc_info()[0]), str(sys.exc_info()[1]))
			raise
		if len(self.rgclM) == 1:
			raise IOError, "Chain has no clusters: " + szChain

	def IclFindR(self, szName, iclBase):
		if not szName: return 0
		ccl = len(self.rgclM) - 1
		for iclLoop in xrange(ccl, 0, -1):
			if self.rgclM[iclLoop].szNameM == szName: return iclLoop
		szNameDir = szName
		if szNameDir[-1] != "/": szNameDir += "/"
		for iclLoop in xrange(ccl, 0, -1):
			if self.rgclM[iclLoop].szBaseDirM == szNameDir: return iclLoop
		for iclLoop in xrange(ccl, 0, -1):
			for ce in self.rgclM[iclLoop].rgceListM:
				if ce.szValM == szNameDir: return iclLoop
		if not re.match(r"-?\d+$", szName): return 0
		iclSrc = int(szName)
		if not iclBase: iclBase = ccl + 1
		if iclSrc <= 0: iclSrc = iclBase + iclSrc
		if iclSrc >= 1 and iclSrc <= ccl: return iclSrc
		return 0

	def OutputR(self, osOut):
		ccl = len(self.rgclM) - 1
		for icl in xrange(1, ccl + 1):
			osOut.write("(%d) " % icl)
			self.rgclM[icl].OutputR(osOut)
			osOut.write("\n")

	def SzOutputR(self):
		rgsz = []
		for cl in self.rgclM[1:]:
			rgsz.append(cl.SzOutputR())
		return ":".join(rgsz)

	def SzFindFileR(szFile, fCreate = False):
		if szFile[:1] == "/" or szFile[:2] == "./":
			while len(szFile) > 2 and szFile[:2] == "./":
				szFile = szFile[2:]
			if os.path.isfile(szFile) or fCreate: return szFile
			else: return None
		szPath = "."
		if os.environ.has_key(Chain.szChainPathVarM):
			szPath = os.environ[Chain.szChainPathVarM]
		if fCreate and os.environ.has_key(Chain.szChainCreateVarM):
			szPath = os.environ[Chain.szChainCreateVarM]
		for szDir in szPath.split(":"):
			if not szDir: continue
			if szDir.split("/")[-1] == ".splitdot":
				szCur = "/".join(szDir.split("/")[:-1])
				for szAdd in szFile.split(".")[:-1]:
					szCur = os.path.join(szCur, szAdd + ".")
				szCur = os.path.join(szCur, szFile)
			else:
				szCur = os.path.join(szDir, szFile)
			if os.path.isfile(szCur) or fCreate: return szCur
		return None
	SzFindFileR = staticmethod(SzFindFileR)


	rgszOneCharTokenM = ["=", ">", "<", "!", "(", ")", "[", "]", ",", "?", ":"]
	rgszTwoCharTokenM = ["==", ">=", "<=", "!="]
	rgszDelimM = rgszOneCharTokenM + ["#", "'", '"']
	rgfOneCharTokenM = {}
	for sz in rgszOneCharTokenM: rgfOneCharTokenM[sz] = True
	rgfTwoCharTokenM = {}
	for sz in rgszTwoCharTokenM: rgfTwoCharTokenM[sz] = True
	rgfDelimM = {}
	for sz in rgszDelimM: rgfDelimM[sz] = True

	def RgszTokenizeR(szSrc):
		rgszRet = []
		ichSrc = 0
		cchSrc = len(szSrc)
		while ichSrc < cchSrc:
			chCur = szSrc[ichSrc]
			if chCur.isspace():
				ichSrc += 1
			elif chCur == "#":
				ichEnd = szSrc.find("\n", ichSrc + 1)
				if ichEnd < 0: break
				ichSrc = ichEnd + 1
			elif chCur == "'" or chCur == '"':
				ichEnd = szSrc.find(chCur, ichSrc + 1)
				if ichEnd < 0:
					raise IOError, "Unterminated quoted string."
				rgszRet.append('"' + szSrc[ichSrc + 1: ichEnd])
				ichSrc = ichEnd + 1
			elif Chain.rgfTwoCharTokenM.has_key(szSrc[ichSrc:ichSrc+2]):
				rgszRet.append(szSrc[ichSrc:ichSrc+2])
				ichSrc += 2
			elif Chain.rgfOneCharTokenM.has_key(chCur):
				rgszRet.append(chCur)
				ichSrc += 1
			else:
				ichBegin = ichSrc
				ichSrc += 1
				while ichSrc < cchSrc and not szSrc[ichSrc].isspace() and \
					not Chain.rgfDelimM.has_key(szSrc[ichSrc]):
					ichSrc += 1
				rgszRet.append("'" + szSrc[ichBegin:ichSrc])
		return rgszRet
	RgszTokenizeR = staticmethod(RgszTokenizeR)

	def GetTokenR(rgszTok, szTok, szErr):
		if not rgszTok or rgszTok[0] != szTok:
			raise IOError, "Expecting '%s' token: %s" % (szTok, szErr)
		rgszTok.pop(0)
	GetTokenR = staticmethod(GetTokenR)

	def FGetTokenR(rgszTok, szTok):
		if not rgszTok or rgszTok[0] != szTok:
			return False
		rgszTok.pop(0)
		return True
	FGetTokenR = staticmethod(FGetTokenR)

	def SzGetVarTokenR(rgszTok, szErr):
		if not rgszTok or rgszTok[0][0] != "'":
			raise IOError, "Expecting name/file: " + szErr
		return rgszTok.pop(0)[1:]
	SzGetVarTokenR = staticmethod(SzGetVarTokenR)

	def SzGetValTokenR(rgszTok, szErr):
		if not rgszTok or (rgszTok[0][0] != "'" and rgszTok[0][0] != '"'):
			raise IOError, "Expecting value: " + szErr
		return rgszTok.pop(0)[1:]
	SzGetValTokenR = staticmethod(SzGetValTokenR)

	def ItyFindSeqR(rgty, ty, ityStart = 0):
		try:
			if not ityStart:
				return rgty.index(ty)
			else:
				return rgty[ityStart:].index(ty) + ityStart
		except:
			return -1
	ItyFindSeqR = staticmethod(ItyFindSeqR)


	def ProcessChain(self, szChain):
		rgszTok = Chain.RgszTokenizeR(szChain)
		rgszTok.append(":")
		iszTok = 0
		cszTok = len(rgszTok)
		while iszTok < cszTok:
			iszEnd = rgszTok[iszTok:].index(":") + iszTok
			rgszClust = rgszTok[iszTok:iszEnd]
			iszTok = iszEnd + 1
			szErr = re.sub(r"['\"]", "", " ".join(rgszClust))

			if Chain.FGetTokenR(rgszClust, "?"):
				fNot = Chain.FGetTokenR(rgszClust, "!")
				szVar = Chain.SzGetVarTokenR(rgszClust, szErr)
				if not rgszClust:
					raise IOError, "Unexpected end of conditional: " + szErr
				elif rgszClust[0] == "?":
					fCond = self.rgszVarM.has_key(szVar)
				else:
					szOp = rgszClust.pop(0)
					szValCur = ""
					if self.rgszVarM.has_key(szVar):
						szValCur = self.rgszVarM[szVar]
					szValCmp = Chain.SzExpandFileNameR( \
						Chain.SzGetValTokenR(rgszClust, szErr), self.rgszVarM)
					if szOp == "=" or szOp == "==":
						fCond = (szValCur == szValCmp)
					elif szOp == "!=":
						fCond = (szValCur != szValCmp)
					else:
						raise IOError, "Invalid op in conditional: " + szErr
				Chain.GetTokenR(rgszClust, "?", szErr)
				if not (fCond ^ fNot): continue
			if not rgszClust: continue

			if Chain.ItyFindSeqR(rgszClust, "(") < 0 and \
				Chain.ItyFindSeqR(rgszClust, "=") >= 0:
				szFeat = Chain.SzGetVarTokenR(rgszClust, szErr)
				Chain.GetTokenR(rgszClust, "=", szErr)
				szVal = Chain.SzExpandFileNameR( \
					Chain.SzGetValTokenR(rgszClust, szErr), self.rgszVarM)
				if szFeat == "file":
					szVal = SzNormFileNameReadG(szVal, self.rgszFileM[-1])
					szFile = Chain.SzFindFileR(szVal)
					if not szFile:
						raise IOError, "Non-existent file/chain: " + szErr
					self.ProcessFile(szFile)
				else:
					self.rgszVarM[szFeat] = szVal
			else:
				szName = None
				if Chain.FGetTokenR(rgszClust, "["):
					szName = Chain.SzGetVarTokenR(rgszClust, szErr)
					Chain.GetTokenR(rgszClust, "]", szErr)
				if len(rgszClust) == 1 and rgszClust[0][0] == "'" and \
					Chain.SzFindFileR(rgszClust[0][1:]):
					szFile = Chain.SzFindFileR( \
						Chain.SzGetVarTokenR(rgszClust, szErr))
					iclName = len(self.rgclM)
					self.ProcessFile(szFile)
					if szName and iclName < len(self.rgclM):
						self.rgclM[iclName].szNameM = szName
				else:
					clCur = Cluster()
					if szName: clCur.szNameM = szName
					self.rgclM.append(clCur)
					clCur.ProcessCluster(rgszClust, self, len(self.rgclM) - 1)
					if not clCur.rgceListM: print >>sys.stderr, \
						"Warning: empty cluster: %s" % szErr + \
						" (perhaps directories do not exist)"
					if not clCur.fOverM:
						for ceCur in clCur.rgceListM:
							if not ceCur.szValM: raise IOError, \
								"Empty directory name for entry '%s': %s" % \
								(ceCur.szFeatM, szErr)
					else:
						self.rgclM.pop()
			if rgszClust:
				raise IOError, "Unexpected tokens at end of cluster: " + szErr

	def ProcessFile(self, szFile):
		isIn = open(szFile)
		szRead = "".join(isIn.readlines())
		isIn.close()
		self.rgszFileM.append(szFile)
		self.ProcessChain(szRead)
		self.rgszFileM.pop()

	def TpHashReposR(self, iclSrc):
		szHash = ""
		for iclLoop in xrange(1, iclSrc + 1):
			cl = self.rgclM[iclLoop]
			for szFeat in ["inc", "src"]:
				if not cl.rgceHashM.has_key(szFeat) or \
					not cl.rgceHashM[szFeat].szValM:
					szHash += "*"
				else:
					szHash += SzAbsPathNameG(cl.rgceHashM[szFeat].szValM, True)
				szHash += " "
		wHash = 0
		for ch in list(szHash):
			wHash = (wHash * 16411 + ord(ch)) & 0xffffffff
		szRepos = ""
		for ich in xrange(5, -1, -1):
			wCur = ((wHash >> (ich * 5)) & 31)
			if wCur < 10: szRepos += chr(ord("0") + wCur)
			else: szRepos += chr(ord("A") + wCur - 10)
		return (szRepos, szHash)

	def ExpandRepos(self):
		ccl = len(self.rgclM) - 1
		for icl in xrange(1, ccl + 1):
			cl = self.rgclM[icl]
			(szRepos, szHash) = self.TpHashReposR(icl)
			for ce in cl.rgceListM:
				if ce.szValM.find("@@") < 0: continue
				ce.szValM = re.sub("@@", szRepos, ce.szValM)
				ce.szReposHashM = szHash
				szCheckFile = os.path.join(ce.szValM, ".repos_key")
				if os.path.exists(szCheckFile):
					isIn = open(szCheckFile)
					szCheck = isIn.readline()[:-1]
					isIn.close()
					if ce.szReposHashM != szCheck:
						print >>sys.stderr, "**Warning**: " + \
							"hash conflict in repos dir: %s" % ce.szValM
						print >>sys.stderr, "  Conflicting keys: [%s], [%s]" % \
							(ce.szReposHashM, szCheck)
						print >>sys.stderr, "  This may cause incorrect builds."

	def FWarnMissingDirsR(self):
		ccl = len(self.rgclM) - 1
		fWarn = False
		rgfWarn = {}
		for icl in xrange(1, ccl + 1):
			cl = self.rgclM[icl]
			for ce in cl.rgceListM:
				if ce.szValM and ce.fExplicitM and \
					not os.path.exists(ce.szValM) and \
					not rgfWarn.has_key(ce.szValM):
					print >>sys.stderr, "*Warning*: directory in chain " + \
						"does not exist: " + ce.szValM
					rgfWarn[ce.szValM] = True
					fWarn = True
		return fWarn

	def CreateDirsR(self):
		ccl = len(self.rgclM) - 1
		for icl in xrange(1, ccl + 1):
			cl = self.rgclM[icl]
			for ce in cl.rgceListM:
				if not ce.szValM or not ce.fExplicitM or \
					os.path.exists(ce.szValM): continue
				szDir = ce.szValM
				if szDir[:1] != "/": szDir = "./" + szDir
				rgszSplit = szDir[:-1].split("/")
				szLastDir = rgszSplit[0] + "/"
				for iszDir in xrange(1, len(rgszSplit)):
					szCurDir = "/".join(rgszSplit[:iszDir+1]) + "/"
					if not os.path.exists(szCurDir):
						print >>sys.stderr, "Creating directory: " + szCurDir
						os.mkdir(szCurDir)
						rgwLast = os.stat(szLastDir)
						os.chmod(szCurDir, rgwLast[stat.ST_MODE])
						os.chown(szCurDir, -1, rgwLast[stat.ST_GID])
					szLastDir = szCurDir
				if ce.szReposHashM:
					szCheckFile = os.path.join(ce.szValM, ".repos_key")
					osOut = open(szCheckFile, "w")
					print >>osOut, ce.szReposHashM
					osOut.close()
					os.chmod(szCheckFile, 0666)

	def CnInitGlobalR():
		if os.environ.has_key("SMK_CHAIN") and os.environ["SMK_CHAIN"]:
			szChain = os.environ["SMK_CHAIN"]
		elif os.path.exists(".smk_chain"):
			szChain = "file=./.smk_chain"
		elif os.path.exists(".mk_chain"):
			szChain = "file=./.mk_chain"
		elif os.environ.has_key("SMK_CHAIN_DEFAULT"):
			szChain = os.environ["SMK_CHAIN_DEFAULT"]
		elif os.environ.has_key("MK_CHAIN"):
			szChain = os.environ["MK_CHAIN"]
		else:
			szChain = "."
		return Chain(szChain)
	CnInitGlobalR = staticmethod(CnInitGlobalR)


########################################################################
#
########################################################################



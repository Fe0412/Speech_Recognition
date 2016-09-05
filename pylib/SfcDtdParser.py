#!/usr/bin/env /speech6/lang/y2k/exec/python


import os, re, sys


class InputFile:
	def __init__(self, szFile, fString = False, szErr = None):
		self.szFileM = szFile
		self.fStringM = fString
		self.szErrM = szErr
		self.ilnM = 1
		self.ichCurM = 0
		self.ichLineM = 1
		if not self.fStringM:
			if not self.szErrM: self.szErrM = "file '%s'" % szFile
			isIn = open(szFile)
			self.szBufM = "".join(isIn.readlines())
			isIn.close()
		else:
			if not self.szErrM: self.szErrM = "included string"
			self.szBufM = szFile
		self.cchM = len(self.szBufM)

	def FConsumeSpace(self):
		fRet = False
		while self.ichCurM < self.cchM and self.szBufM[self.ichCurM].isspace():
			if self.szBufM[self.ichCurM] == "\n":
				self.ilnM += 1
				self.ichLineM = 1
			else:
				self.ichLineM += 1
			self.ichCurM += 1
			fRet = True
		return fRet

	def Advance(self, cch):
		assert self.ichCurM + cch <= self.cchM
		for ichLoop in xrange(cch):
			if self.szBufM[self.ichCurM] == "\n":
				self.ilnM += 1
				self.ichLineM = 1
			else:
				self.ichLineM += 1
			self.ichCurM += 1


class InputBuffer:
	def __init__(self, szFile, fString = False, szErr = None):
		self.rgfiM = []
		self.rgfiM.append(InputFile(szFile, fString, szErr))

	def WarningR(self, szWarn):
		print >>sys.stderr, "*Warning*: %s" % szWarn
		rgfi = self.rgfiM
		if not rgfi:
			print >>sys.stderr, "  Located at EOF: " + szFile
		else:
			print >>sys.stderr, "  Located at line %d.%d: %s" % \
				(rgfi[-1].ilnM, rgfi[-1].ichLineM, rgfi[-1].szErrM)
			for ifi in xrange(len(rgfi) - 2, -1, -1):
				print >>sys.stderr, "  Included at line %d in %s" % \
					(rgfi[ifi].ilnM, rgfi[ifi].szErrM)

	def PushFile(self, szFile, fString = False, szErr = None):
		self.rgfiM.append(InputFile(szFile, fString, szErr))

	def PopFile(self):
		assert self.rgfiM and self.rgfiM[-1].ichCurM == self.rgfiM[-1].cchM
		self.rgfiM.pop()

	def SzNormDirR(self):
		for ifi in xrange(len(self.rgfiM) - 1, -1, -1):
			fiCur = self.rgfiM[ifi]
			if not fiCur.fStringM:
				szDir = os.path.dirname(fiCur.szFileM)
				if not szDir: szDir = "."
				return szDir
		return "."

	def SzLookaheadR(self, cch):
		if not self.rgfiM: return ""
		fiCur = self.rgfiM[-1]
		return fiCur.szBufM[fiCur.ichCurM:fiCur.ichCurM+cch]

	def MoLookaheadR(self, reSrc, fAllowSpace = False):
		if not self.rgfiM: return None
		fiCur = self.rgfiM[-1]
		moRet = reSrc.match(fiCur.szBufM, fiCur.ichCurM)
		if not fAllowSpace and moRet and __debug__:
			for ch in list(moRet.group()):
				assert not ch.isspace()
		return moRet

	def FLookaheadR(self, szSrc):
		if not self.rgfiM: return False
		fiCur = self.rgfiM[-1]
		return fiCur.szBufM[fiCur.ichCurM:fiCur.ichCurM+len(szSrc)] == szSrc

	def FConsume(self, szSrc, fMust = False):
		if not self.FLookaheadR(szSrc):
			if fMust: raise IOError, "Expected token: " + szSrc
			return False
		self.rgfiM[-1].Advance(len(szSrc))
		return True

	def SzConsumePattern(self, reSrc, szErr = None, fAllowSpace = False):
		mo = self.MoLookaheadR(reSrc, fAllowSpace)
		if not mo:
			if szErr: raise IOError, "Expected '%s'." % szErr
			return None
		self.rgfiM[-1].Advance(len(mo.group()))
		return mo.group()

	def SzConsumeUntil(self, szEnd, szErr = None):
		if self.rgfiM:
			fiCur = self.rgfiM[-1]
			ichFind = fiCur.szBufM.find(szEnd, fiCur.ichCurM)
			if ichFind >= 0:
				szRet = fiCur.szBufM[fiCur.ichCurM:ichFind]
				fiCur.Advance(ichFind - fiCur.ichCurM)
				return szRet
		if szErr:
			raise IOError, "Expected '%s' to close '%s'." % (szEnd, szErr)
		return None


class DtdParser:
	#	restrict to chars <= 127
	reNameM = re.compile(r"[a-zA-Z_:][a-zA-Z0-9._:-]*")
	reXmlM = re.compile(r"[Xx][Mm][Ll]$")
	reSystemLiteralM = re.compile(r"""("[^"]*")|('[^']*')""")
	rePubidLiteralM = re.compile(r"""("[\sa-zA-Z0-9'()+,./:=?;!*#@$_%-]*")|('[\sa-zA-Z0-9()+,./:=?;!*#@$_%-]*')""")
	reDigitStringM = re.compile(r"[0-9]+")
	reHexDigitStringM = re.compile(r"[0-9a-fA-F]+")
	rePERefM = re.compile(r"%[a-zA-Z_:][a-zA-Z0-9._:-]*;")
	reVersionNumM = re.compile(r"[a-zA-Z0-9_.:-]+")
	reEncNameM = re.compile(r"[A-Za-z][A-Za-z0-9._-]*")
	reNmTokenM = re.compile(r"[a-zA-Z0-9._:-]+")
	reCommentM = re.compile(r"([^-]|-[^-])*")
	wInternalE = 1
	wExternalE = 2

	def __init__(self):
		self.bfM = None
		self.szVersionNumM = None
		self.szEncodingM = None
		self.rgtpNotationM = {}
		self.rgtpParamM = {}
		self.rgtpGeneralM = {
			"lt": (DtdParser.wInternalE, "&#38;#60;"),
			"gt": (DtdParser.wInternalE, "&#62;"),
			"amp": (DtdParser.wInternalE, "&#38;#38;"),
			"apos": (DtdParser.wInternalE, "&#39;"),
			"quot": (DtdParser.wInternalE, "&#34;")
			}
		self.rgtpElemM = {}
		self.rg2tpAttrM = {}

	def FConsumeSpace(self, fMust = False, fSkipExpand = False):
		fRet = False
		bf = self.bfM
		while True:
			while bf.rgfiM:
				fRet |= bf.rgfiM[-1].FConsumeSpace()
				if bf.rgfiM[-1].ichCurM < bf.rgfiM[-1].cchM: break
				bf.PopFile()
			if fSkipExpand: break
			mo = self.bfM.MoLookaheadR(DtdParser.rePERefM)
			if not mo: break
			bf.FConsume(mo.group(), True)
			szName = mo.group()[1:-1]
			if not self.rgtpParamM.has_key(szName):
				raise IOError, "Invalid parameter reference: " + szName
			tpCur = self.rgtpParamM[szName]
			if tpCur[0] != DtdParser.wInternalE: raise IOError, \
				"External parameter ref not allowed here: " + szName
			bf.PushFile(" %s " % tpCur[1], True, "entity '%s'" % szName)
		if fMust and not fRet: raise IOError, "Expected space."
		return fRet

	#	rule 77; p. 37
	def FParseTextDecl(self):
		if not self.bfM.FConsume("<?xml"): return False
		self.FConsumeSpace(True)
		if self.bfM.FConsume("version"):
			self.FConsumeSpace()
			self.bfM.FConsume("=", True)
			self.FConsumeSpace()
			chQuote = self.bfM.SzLookaheadR(1)
			if chQuote != "'" and chQuote != '"':
				raise IOError, "Expected quote."
			self.bfM.FConsume(chQuote, True)
			self.szVersionNumM = \
				self.bfM.SzConsumePattern(DtdParser.reVersionNumM, "VersionNum")
			self.bfM.FConsume(chQuote, True)
			self.FConsumeSpace(True)
		self.bfM.FConsume("encoding", True)
		self.FConsumeSpace()
		self.bfM.FConsume("=", True)
		self.FConsumeSpace()
		chQuote = self.bfM.SzLookaheadR(1)
		if chQuote != "'" and chQuote != '"':
			raise IOError, "Expected quote."
		self.bfM.FConsume(chQuote, True)
		self.szEncodingM = self.bfM.SzConsumePattern(DtdParser.reEncNameM,
			"EncName")
		self.bfM.FConsume(chQuote, True)
		self.FConsumeSpace()
		self.bfM.FConsume("?>", True)
		return True

	#	rule 47/48; p. 22
	def TpParseElemContent(self, fRoot = False):
		rgszRet = []
		rgszParse = []
		if fRoot or self.bfM.FConsume("("):
			rgszRet.append("(")
			self.FConsumeSpace()
			(szFirst, rgszFirst) = self.TpParseElemContent()
			rgszRet.extend(szFirst.split())
			self.FConsumeSpace()
			if self.bfM.FLookaheadR("|"):
				rgszParse = ["<CHOICE>", rgszFirst]
				while self.bfM.FConsume("|"):
					rgszRet.append("|")
					self.FConsumeSpace()
					(szNext, rgszNext) = self.TpParseElemContent()
					self.FConsumeSpace()
					rgszRet.extend(szNext.split())
					rgszParse.append(rgszNext)
			else:
				if self.bfM.FLookaheadR(","):
					rgszParse = ["<SEQ>", rgszFirst]
				else:
					rgszParse = rgszFirst
				while self.bfM.FConsume(","):
					rgszRet.append(",")
					self.FConsumeSpace()
					(szNext, rgszNext) = self.TpParseElemContent()
					self.FConsumeSpace()
					rgszRet.extend(szNext.split())
					rgszParse.append(rgszNext)
			self.bfM.FConsume(")", True)
			rgszRet.append(")")
		else:
			szName = self.bfM.SzConsumePattern(DtdParser.reNameM, "Name")
			rgszRet.append(szName)
			rgszParse = [szName]
		chPeek = self.bfM.SzLookaheadR(1)
		if chPeek == "?" or chPeek == "*" or chPeek == "+":
			self.bfM.FConsume(chPeek, True)
			rgszRet.append(chPeek)
			rgszParse = ["<%s>" % chPeek, rgszParse]
		return (" ".join(rgszRet), rgszParse)

	#	rule 45; p. 21
	def FParseElementDecl(self):
		if not self.bfM.FConsume("<!ELEMENT"): return False
		self.FConsumeSpace(True)
		szName = self.bfM.SzConsumePattern(DtdParser.reNameM, "Name")
		if self.rgtpElemM.has_key(szName):
			raise IOError, "Duplicate definition for element: " + szName
		self.FConsumeSpace(True)
		szValue = ""
		rgszParse = None
		if self.bfM.FConsume("EMPTY"):
			szValue = "EMPTY"
			rgszParse = ["<EMPTY>"]
		elif self.bfM.FConsume("ANY"):
			szValue = "ANY"
			rgszParse = ["<ANY>"]
		else:
			self.bfM.FConsume("(", True)
			self.FConsumeSpace()
			if self.bfM.FConsume("#PCDATA"):
				self.FConsumeSpace()
				if self.bfM.FLookaheadR("|"):
					szValue = "( #PCDATA"
					rgszParse = ["<MIXED>", "#PCDATA"]
					while self.bfM.FConsume("|"):
						self.FConsumeSpace()
						szOr = self.bfM.SzConsumePattern(DtdParser.reNameM,
							"Name")
						self.FConsumeSpace()
						szValue += " | %s" % szOr
						rgszParse.append(szOr)
					self.bfM.FConsume(")*", True)
					szValue += " ) *"
				else:
					self.bfM.FConsume(")", True)
					szValue = "( #PCDATA )"
					rgszParse = ["<#PCDATA>"]
			else:
				(szValue, rgszParse) = self.TpParseElemContent(True)
		self.rgtpElemM[szName] = (szValue, rgszParse)
		self.FConsumeSpace()
		self.bfM.FConsume(">", True)
		return True

	#	rule 10; p. 9
	def SzParseAttValue(self):
		chQuote = self.bfM.SzLookaheadR(1)
		if chQuote != "'" and chQuote != '"':
			raise IOError, "Expected quote."
		self.bfM.FConsume(chQuote, True)
		szRet = ""
		while True:
			chPeek = self.bfM.SzLookaheadR(1)
			if not chPeek: raise IOError, "Unterminated attribute value."
			if chPeek == chQuote: break
			if chPeek == "<":
				raise IOError, "Invalid char '<' in attribute value."
			self.bfM.FConsume(chPeek, True)
			if chPeek == "&":
				if self.bfM.FConsume("#"):
					if self.bfM.FConsume("x"):
						szVal = "x" + self.bfM.SzConsumePattern( \
							DtdParser.reHexDigitStringM, "HexDigitString")
					else:
						szVal = self.bfM.SzConsumePattern( \
							DtdParser.reDigitStringM, "DigitString")
					self.bfM.FConsume(";", True)
					szRet += "&#%s;" % szVal
				else:
					szName = self.bfM.SzConsumePattern(DtdParser.reNameM,
						"Name")
					self.bfM.FConsume(";", True)
					if not self.rgtpGeneralM.has_key(szName):
						raise IOError, "Invalid general reference: " + szName
					tpCur = self.rgtpGeneralM[szName]
					if tpCur[0] != DtdParser.wInternalE: raise IOError, \
						"External general ref invalid here: " + szName
					szRet += tpCur[1]
			else:
				szRet += chPeek
		self.bfM.FConsume(chQuote, True)
		return szRet

	#	rule 52; p. 24
	def FParseAttListDecl(self):
		if not self.bfM.FConsume("<!ATTLIST"): return False
		self.FConsumeSpace(True)
		szElem = self.bfM.SzConsumePattern(DtdParser.reNameM, "Name")
		if not self.rg2tpAttrM.has_key(szElem):
			self.rg2tpAttrM[szElem] = {}
		rgtp = self.rg2tpAttrM[szElem]
		while True:
			fSpace = self.FConsumeSpace()
			if not fSpace or self.bfM.FLookaheadR(">"): break
			szAttr = self.bfM.SzConsumePattern(DtdParser.reNameM, "Name")
			self.FConsumeSpace(True)
			szAttType = None
			rgszEnum = []
			szDefType = None
			szDefVal = None
			if self.bfM.FConsume("CDATA"):
				szAttType = "CDATA"
			elif self.bfM.FConsume("IDREFS"):
				szAttType = "IDREFS"
			elif self.bfM.FConsume("IDREF"):
				szAttType = "IDREF"
			elif self.bfM.FConsume("ID"):
				szAttType = "ID"
			elif self.bfM.FConsume("ENTITIES"):
				szAttType = "ENTITIES"
			elif self.bfM.FConsume("ENTITY"):
				szAttType = "ENTITY"
			elif self.bfM.FConsume("NMTOKENS"):
				szAttType = "NMTOKENS"
			elif self.bfM.FConsume("NMTOKEN"):
				szAttType = "NMTOKEN"
			elif self.bfM.FConsume("NOTATION"):
				szAttType = "NOTATION"
				self.FConsumeSpace(True)
				self.bfM.FConsume("(", True)
				self.FConsumeSpace()
				while True:
					szNotation = self.bfM.SzConsumePattern(DtdParser.reNameM,
						"Name")
					if not self.rgtpNotationM.has_key(szNotation):
						raise IOError, "Invalid notation: " + szNotation
					rgszEnum.append(szNotation)
					self.FConsumeSpace()
					if self.bfM.FConsume(")"): break
					self.bfM.FConsume("|", True)
					self.FConsumeSpace()
			elif self.bfM.FConsume("("):
				szAttType = "ENUM"
				self.FConsumeSpace()
				while True:
					szToken = self.bfM.SzConsumePattern(DtdParser.reNmTokenM,
						"Nmtoken")
					rgszEnum.append(szToken)
					self.FConsumeSpace()
					if self.bfM.FConsume(")"): break
					self.bfM.FConsume("|", True)
					self.FConsumeSpace()
			else:
				raise IOError, "Invalid attribute type."
			self.FConsumeSpace(True)
			if self.bfM.FConsume("#REQUIRED"):
				szDefType = "#REQUIRED"
			elif self.bfM.FConsume("#IMPLIED"):
				szDefType = "#IMPLIED"
			else:
				if self.bfM.FConsume("#FIXED"):
					szDefType = "#FIXED"
					self.FConsumeSpace(True)
				szDefVal = self.SzParseAttValue()
			if not rgtp.has_key(szAttr):
				rgtp[szAttr] = (szAttType, rgszEnum, szDefType, szDefVal)
		self.bfM.FConsume(">", True)
		return True

	#	rule 9; p. 9
	def SzParseEntityValue(self):
		chQuote = self.bfM.SzLookaheadR(1)
		assert chQuote == "'" or chQuote == '"'
		self.bfM.FConsume(chQuote, True)
		szRet = ""
		while True:
			chPeek = self.bfM.SzLookaheadR(1)
			if not chPeek: raise IOError, "Unterminated entity value."
			if chPeek == chQuote: break
			self.bfM.FConsume(chPeek, True)
			if chPeek == "%":
				szName = self.bfM.SzConsumePattern(DtdParser.reNameM, "Name")
				self.bfM.FConsume(";", True)
				if not self.rgtpParamM.has_key(szName):
					raise IOError, "Invalid parameter reference: " + szName
				tpCur = self.rgtpParamM[szName]
				if tpCur[0] != DtdParser.wInternalE: raise IOError, \
					"External parameter ref not supported here: " + szName
				szRet += tpCur[1]
			elif chPeek == "&":
				if self.bfM.FConsume("#"):
					if self.bfM.FConsume("x"):
						szVal = "x" + self.bfM.SzConsumePattern( \
							DtdParser.reHexDigitStringM, "HexDigitString")
					else:
						szVal = self.bfM.SzConsumePattern( \
							DtdParser.reDigitStringM, "DigitString")
					self.bfM.FConsume(";", True)
					szRet += "&#%s;" % szVal
				else:
					szName = self.bfM.SzConsumePattern(DtdParser.reNameM,
						"Name")
					self.bfM.FConsume(";", True)
					szRet += "&%s;" % szName
			else:
				szRet += chPeek
		self.bfM.FConsume(chQuote, True)
		return szRet

	#	rule 70; p. 35
	def FParseEntityDecl(self):
		if not self.bfM.FConsume("<!ENTITY"): return False
		self.FConsumeSpace(True)
		fGeneral = False
		fExternal = False
		szPublic = None
		szSystem = None
		szValue = None
		if self.bfM.FConsume("%"):
			self.FConsumeSpace(True)
			szEntity = self.bfM.SzConsumePattern(DtdParser.reNameM, "Name")
			self.FConsumeSpace(True)
		else:
			fGeneral = True
			szEntity = self.bfM.SzConsumePattern(DtdParser.reNameM, "Name")
			self.FConsumeSpace(True)

		chPeek = self.bfM.SzLookaheadR(1)
		if chPeek == "'" or chPeek == '"':
			szValue = self.SzParseEntityValue()
		elif chPeek == "S":
			fExternal = True
			self.bfM.FConsume("SYSTEM", True)
			self.FConsumeSpace(True)
			szSystem = self.bfM.SzConsumePattern(DtdParser.reSystemLiteralM,
				"SystemLiteral", True)[1:-1]
		elif chPeek == "P":
			fExternal = True
			self.bfM.FConsume("PUBLIC", True)
			self.FConsumeSpace(True)
			szPublic = self.bfM.SzConsumePattern(DtdParser.rePubidLiteralM,
				"PubidLiteral", True)[1:-1]
			self.FConsumeSpace(True)
			szSystem = self.bfM.SzConsumePattern(DtdParser.reSystemLiteralM,
				"SystemLiteral", True)[1:-1]
		else:
			raise IOError, "Invalid entity value."

		szNotation = None
		if fGeneral and fExternal:
			fSpace = self.FConsumeSpace()
			if fSpace and self.bfM.FConsume("NDATA"):
				self.FConsumeSpace(True)
				szNotation = self.bfM.SzConsumePattern(DtdParser.reNameM,
					"Name")
				if not self.rgtpNotationM.has_key(szNotation):
					raise IOError, "Invalid notation: " + szNotation
		if fGeneral: rgtp = self.rgtpGeneralM
		else: rgtp = self.rgtpParamM
		if not rgtp.has_key(szEntity):
			if not fExternal:
				rgtp[szEntity] = (DtdParser.wInternalE, szValue)
			else:
				rgtp[szEntity] = (DtdParser.wExternalE, szPublic, szSystem,
					szNotation)
		self.FConsumeSpace()
		self.bfM.FConsume(">", True)
		return True

	#	rule 82; p. 44
	def FParseNotationDecl(self):
		if not self.bfM.FConsume("<!NOTATION"): return False
		self.FConsumeSpace(True)
		szName = self.bfM.SzConsumePattern(DtdParser.reNameM, "Name")
		self.FConsumeSpace(True)
		if self.rgtpNotationM.has_key(szName):
			raise IOError, "Duplicate notation decl: " + szName
		szPublic = None
		szSystem = None
		if self.bfM.FConsume("SYSTEM"):
			self.FConsumeSpace(True)
			szSystem = self.bfM.SzConsumePattern(DtdParser.reSystemLiteralM,
				"SystemLiteral", True)[1:-1]
		elif self.bfM.FConsume("PUBLIC"):
			self.FConsumeSpace(True)
			szPublic = self.bfM.SzConsumePattern(DtdParser.rePubidLiteralM,
				"PubidLiteral", True)[1:-1]
			fSpace = self.FConsumeSpace()
			chPeek = self.bfM.SzLookaheadR(1)
			if fSpace and (chPeek == "'" or chPeek == '"'):
				szSystem = self.bfM.SzConsumePattern(DtdParser.reSystemLiteralM,
					"SystemLiteral", True)[1:-1]
		else:
			raise IOError, "Expected 'SYSTEM' or 'PUBLIC'."
		self.rgtpNotationM[szName] = (szPublic, szSystem)
		self.FConsumeSpace()
		self.bfM.FConsume(">", True)
		return True

	#	rule 16; p. 10
	def FParsePI(self):
		if not self.bfM.FConsume("<?"): return False
		szName = self.bfM.SzConsumePattern(DtdParser.reNameM)
		if not szName or DtdParser.reXmlM.match(szName):
			raise IOError, "Expected 'PITarget'."
		if self.FConsumeSpace():
			self.bfM.SzConsumeUntil("?>", "PI")
		self.bfM.FConsume("?>", True)
		return True

	#	rule 15; p. 10
	def FParseComment(self):
		if not self.bfM.FConsume("<!--"): return False
		self.bfM.SzConsumePattern(DtdParser.reCommentM, "Comment", True)
		self.bfM.FConsume("-->", True)
		return True

	#	rule 29; p. 13
	def FParseMarkupDecl(self):
		return self.FParseElementDecl() or \
			self.FParseAttListDecl() or \
			self.FParseEntityDecl() or \
			self.FParseNotationDecl() or \
			self.FParsePI() or \
			self.FParseComment()

	#	rule 61; p. 31
	def FParseConditionalSect(self):
		if not self.bfM.FConsume("<!["): return False
		self.FConsumeSpace()
		if self.bfM.FConsume("INCLUDE"):
			fIgnore = False
		elif self.bfM.FConsume("IGNORE"):
			fIgnore = True
		else:
			raise IOError, "Expected 'INCLUDE' or 'IGNORE'."
		self.FConsumeSpace()
		self.bfM.FConsume("[", True)
		if fIgnore:
			cevNest = 0
			while True:
				chPeek = self.bfM.SzLookaheadR(1)
				if not chPeek:
					raise IOError, "Unterminated conditional construct."
				if chPeek == "<" and self.bfM.FConsume("<!["):
					cevNest += 1
				elif chPeek == "]" and self.bfM.FConsume("]]>"):
					cevNest -= 1
					if cevNest < 0: break
				else:
					self.bfM.FConsume(chPeek, True)
		else:
			if not self.FParseExtSubsetDecl():
				raise IOError, "Expected 'ExtSubsetDecl'."
			self.bfM.FConsume("]]>", True)
		return True

	#	rule 28a; p. 13
	def FParseDeclSep(self):
		if self.FConsumeSpace(False, True): return True
		if not self.bfM.FConsume("%"): return False
		szName = self.bfM.SzConsumePattern(DtdParser.reNameM, "Name")
		self.bfM.FConsume(";", True)
		if not self.rgtpParamM.has_key(szName):
			raise IOError, "Invalid parameter entity: " + szName
		tpCur = self.rgtpParamM[szName]
		if tpCur[0] == DtdParser.wInternalE:
			self.bfM.PushFile(" %s " % tpCur[1], True, "entity '%s'" % szName)
		else:
			if tpCur[3]:
				raise IOError, "Cannot use unparsed reference here."
			szUrl = tpCur[2]
			if szUrl.find(":") < 0 or szUrl[:5] == "file:":
				szFile = szUrl
				if szFile[:5] == "file:": szFile = szFile[5:]
				if szFile[:1] != "/":
					szFile = os.path.join(self.bfM.SzNormDirR(), szFile)
				self.bfM.PushFile(szFile)
			else: raise IOError, \
				"Remote URL ref's not supported yet: " + tpCur[2]
		return True

	#	rule 31; p. 14
	def FParseExtSubsetDecl(self):
		while self.FParseMarkupDecl() or self.FParseConditionalSect() or \
			self.FParseDeclSep():
			pass
		return True

	#	rule 30; p. 14
	def ParseFile(self, szFile):
		self.bfM = InputBuffer(szFile)
		try:
			self.FParseTextDecl()
			if not self.FParseExtSubsetDecl():
				raise IOError, "Expected 'ExtSubsetDecl'."
			if self.bfM.rgfiM:
				raise IOError, "Unexpected text at end of file."
		except:
			rgfi = self.bfM.rgfiM
			if not rgfi:
				print >>sys.stderr, "Syntax error at EOF: " + szFile
			else:
				print >>sys.stderr, "Syntax error at line %d.%d: %s" % \
					(rgfi[-1].ilnM, rgfi[-1].ichLineM, rgfi[-1].szErrM)
				for ifi in xrange(len(rgfi) - 2, -1, -1):
					print >>sys.stderr, "  Included at line %d in %s" % \
						(rgfi[ifi].ilnM, rgfi[ifi].szErrM)
			raise



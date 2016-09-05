#!/usr/bin/env /lang/y2k/exec/python


import sys

class Tokenizer:
	def __init__(self, szSrc):
		self.szSrcM = szSrc
		self.ichM = 0
		self.cchM = len(szSrc)
	def SzGetToken(self):
		while self.ichM < self.cchM:
			chCur = self.szSrcM[self.ichM]
			ichBegin = self.ichM
			if chCur.isspace():
				self.ichM += 1
			elif chCur == "[":
				ichFind = self.szSrcM[self.ichM+1:].find("]")
				if ichFind < 0: sys.exit("Unclosed bracket expr.")
				self.ichM += ichFind + 2
			elif chCur == "/" and self.ichM + 1 < self.cchM and \
				self.szSrcM[self.ichM + 1] == "*":
				ichFind = self.szSrcM[self.ichM+2:].find("*/")
				if ichFind < 0: sys.exit("Unclosed comment expr.")
				self.ichM += ichFind + 4
			elif chCur.isdigit() or (chCur == "-" and \
				self.ichM + 1 < self.cchM and \
				self.szSrcM[self.ichM + 1].isdigit()):
				if chCur == "-": self.ichM += 1
				while self.ichM < self.cchM and \
					self.szSrcM[self.ichM].isdigit(): self.ichM += 1
				return self.szSrcM[ichBegin:self.ichM] 
			else:
				self.ichM += 1
				return chCur
		return None
	def ReadChar(self, chSrc):
		szTok = self.SzGetToken()
		if szTok != chSrc:
			sys.exit("Expected '%s', not '%s'." % (chSrc, szTok))
	def WReadInt(self):
		return int(self.SzGetToken())

class Graph:
	pass

class Node:
	pass

def RggrParsePhoneGraphsG(szSrc):
	tk = Tokenizer(szSrc)
	rggr = []
	cgrTot = tk.WReadInt()
	tk.ReadChar(":")
	for igrCur in xrange(cgrTot):
		grCur = Graph()
		if tk.WReadInt() != igrCur: sys.exit("Out-of-order graph index.")
		tk.ReadChar("=")
		cndTot = tk.WReadInt()
		tk.ReadChar(":")
		grCur.rgndM = []
		grCur.ifnMinM = None
		grCur.ifnMaxM = None
		for indCur in xrange(cndTot):
			ndCur = Node()
			if tk.WReadInt() != indCur: sys.exit("Out-of-order node index.")
			tk.ReadChar("=")
			ndCur.idNodeM = tk.WReadInt()
			tk.ReadChar(",")
			carNull = tk.WReadInt()
			tk.ReadChar(":")
			ndCur.rgarM = []
			for iarNull in xrange(carNull):
				indDst = tk.WReadInt()
				if indDst < 0 or indDst > cndTot:
					sys.exit("Out-of-bounds node.")
				ndCur.rgarM.append((indDst, -1))
			tk.ReadChar(";")
			carData = tk.WReadInt()
			tk.ReadChar(":")
			for iarData in xrange(carData):
				tk.ReadChar("(")
				indDst = tk.WReadInt()
				if indDst < 0 or indDst > cndTot:
					sys.exit("Out-of-bounds node.")
				tk.ReadChar(",")
				idArc = tk.WReadInt()
				tk.ReadChar(")")
				ndCur.rgarM.append((indDst, idArc))
				if grCur.ifnMinM == None or idArc < grCur.ifnMinM:
					grCur.ifnMinM = idArc
				if grCur.ifnMaxM == None or idArc + 1 > grCur.ifnMaxM:
					grCur.ifnMaxM = idArc + 1
			tk.ReadChar(";")
			grCur.rgndM.append(ndCur)
		tk.ReadChar(";")
		rggr.append(grCur)
	tk.ReadChar(";")
	if tk.SzGetToken() != None: sys.exit("Expected EOF.")
	return rggr



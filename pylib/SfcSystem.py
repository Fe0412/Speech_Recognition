#!/usr/bin/env /lang/y2k/exec/python


import os, sys, __main__

def TyCondG(f, ty1, ty2):
	"""Like C ?: ternary operator."""
	if f: return ty1
	else: return ty2

def IchPrintLinesG(osSrc, szOut, cchIndent = 0, ichLine = 0, fAddSpace = 0,
	fNewLine = 1, szEol = "", cchLineMax = -4):
	"""Print (long) string to a file, with automatic line-breaking."""
	cchColumns = 80
	if cchLineMax <= 0:
		cchLineMax = cchColumns + cchLineMax

	rgsz = szOut.split()
	for szTok in rgsz:
		cchTok = len(szTok)
		cchSpace = TyCondG(fAddSpace, 1, 0)
		if ichLine + cchSpace + cchTok > cchLineMax:
			osSrc.write(szEol + "\n" + (" " * cchIndent))
			ichLine = cchIndent
			fAddSpace = 0

		cchSpace = TyCondG(fAddSpace, 1, 0)
		osSrc.write(TyCondG(fAddSpace, " ", "") + szTok)
		ichLine += cchSpace + cchTok
		fAddSpace = 1

	if fNewLine and (ichLine > 0):
		osSrc.write("\n")
		ichLine = 0;
	return ichLine

def SystemG(szCmd, fEcho = 1):
	"""Call system(), exit if error."""
	if fEcho:
		IchPrintLinesG(sys.stdout, szCmd, 2, 0, 0, 1, " \\")
		sys.stdout.flush()
	wWait = os.system(szCmd)
	isig = wWait & 0x7f
	wStatus = wWait >> 8
	if isig: sys.exit("  Command killed by signal: %d." % isig)
	if wStatus: sys.exit("  Command returned nonzero status: %d." % wStatus)

def RunShellCodeG(szCode, szShell = "sh", dict = __main__.__dict__):
	szCode += "\n"
	szOut = ""
	while szCode:
		ichDollar = szCode.find("$")
		if (ichDollar < 0) or (ichDollar + 1 >= len(szCode)):
			szOut += szCode
			szCode = ""
			break
		szOut += szCode[:ichDollar]
		chNext = szCode[ichDollar + 1]
		if chNext == "{":
			ichEnd = szCode.find("}", ichDollar + 2)
			if ichEnd < 0:
				szOut += szCode[ichDollar:ichDollar+2]
				szCode = szCode[ichDollar+2:]
			else:
				ichEnd += 1
				szVar = szCode[ichDollar+2:ichEnd-1]
				if dict.has_key(szVar):
					szOut += str(dict[szVar])
				else:
					szOut += szCode[ichDollar:ichEnd]
				szCode = szCode[ichEnd:]
		elif chNext.isalpha() or (chNext == "_"):
			ichEnd = ichDollar + 2
			while (ichEnd < len(szCode)) and szCode[ichEnd].isalpha():
				ichEnd += 1
			szVar = szCode[ichDollar+1:ichEnd]
			if dict.has_key(szVar):
				szOut += str(dict[szVar])
			else:
				szOut += szCode[ichDollar:ichEnd]
			szCode = szCode[ichEnd:]
		else:
			szOut += szCode[ichDollar:ichDollar+1]
			szCode = szCode[ichDollar+1:]
	osShell = os.popen(szShell, "w")
	osShell.write(szOut)
	osShell.close()



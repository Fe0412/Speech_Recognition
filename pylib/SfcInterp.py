#!/usr/bin/env /lang/y2k/exec/python


import __main__
import re

reEscape = re.compile(r'([^\$]*)\$(\$|[_\w]+|\{[^\}]+\}|\[[^\]]+\])')
reFormat = re.compile(r':(\S+)$')

def SzInterpG(szSrc, dict = __main__.__dict__):
	'''Interpolate variables within a string.'''
	szDst = ''
	while (1):
		moSrc = reEscape.match(szSrc)
		if moSrc is None: break
		szDst += moSrc.group(1)
		szArg = moSrc.group(2)
		if szArg[0] == '$': szDst += '$'
		elif (szArg[0] == '{') or (szArg[0] == '['):
			szExpr = szArg[1:-1]
			moFormat = reFormat.search(szExpr)
			if moFormat is not None:
				szFormat = moFormat.group(1)
				szExpr = szExpr[:moFormat.start(1) - 1]
				szDst += ('%' + szFormat) % eval(szExpr, dict, {})
			else:
				szDst += str(eval(szExpr, dict, {}))
		else: szDst += str(eval(szArg, dict, {}))
		szSrc = szSrc[moSrc.end(2):]
	szDst += szSrc
	return szDst



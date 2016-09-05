#!/usr/bin/env /speech6/lang/y2k/exec/python


import os


def SzCurDirG(fSlash = False):
	szRet = os.getcwd()
	if os.environ.has_key("PWD"):
		szPwd = os.path.normpath(os.environ["PWD"])
		if szPwd[:1] == "/" and os.path.samefile(szPwd, szRet): szRet = szPwd
	if fSlash and szRet[-1:] != "/": szRet += "/"
	return szRet

def SzAbsPathNameG(szPath, fSlash = False):
	if not szPath: return SzCurDirG(fSlash)
	if szPath[:1] == "/":
		szRet = szPath
	elif szPath[:1] == "~":
		szRet = os.path.expanduser(szPath)
	else:
		szRet = SzCurDirG(True) + szPath
	szRet = os.path.normpath(szRet)
	if fSlash and szRet[-1:] != "/": szRet += "/"
	return szRet



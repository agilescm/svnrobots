# -*- coding: utf-8 -*-
'''
uses to sync subversion revisions from one branch to another.
if merge with conflicts, it will create a patch in bin directory,
if merge without conflicts, it will commit changes into subversion repository.

depends:
	subversion commandline client.

yunshan @ 2012.12
'''

import httplib, sys, os, re, time, subprocess
import shutil
import getopt

# debug toggle
debug = True

class SVNMerger(object):
	'''
	Class use to work with two branches merge.
	'''
	def __init__(self):
		'''init class properties'''
		self.go = True
		self.conflicts = 0
		self.output = 'bin'
		self.source = ''
		self.dest = ''
		self.workspace = ''
		self.help = False

		try:
			opts, args = getopt.getopt(sys.argv[1:], "u:p:s:d:h", ["username=", "passwd=",'source=','dest=','help'])

			for x, y in opts:
				if x in ('-u', '--username'):
					self.username = y
				elif x in ('-p', '--passwd'):
					self.passwd = y
				elif x in ('-s', '--source'):
					self.source = y
				elif x in ('-d', '--dest'):
					self.dest = y
				elif x in ('-h', '--help'):
					self.help = True

			self.workspace = self.getURLTail(self.dest)
			# create temp
			if not os.path.exists('temp'):
				os.makedirs('temp')
			else:
				shutil.rmtree('temp')
				os.makedirs('temp')

			if not os.path.exists(self.output):
				os.makedirs(self.output)
			else:
				shutil.rmtree(self.output)
				os.makedirs(self.output)

		except Exception, e:
			# the params was wrong, init as null
			print(e)
			sys.exit(1)

	def __del__(self):
		try:
			shutil.rmtree('temp')
		except Exception, e:
			print(e)

	def svnCheckout(self):
		'''
		do subversion checkout.
		ret = True, checkout successful
		ret = False, checkout failed
		'''
		ret = False

		if self.go:
			cmdsvn = 'svn co ' + self.dest + ' temp/' + self.workspace
			outsvn = self.runCommand(cmdsvn)
			if debug:
				print(outsvn)

			if 'Checked out revision' in outsvn:
				ret = True

		return ret

	def checkConflict(self):
		'''check whether conflicts exist, return num of conflicts'''
		retConflicts = 0

		if debug:
			print('def checkConflict:\n')

		if self.go:
			if os.path.exists('temp/' + self.workspace):
				cmdsvn = 'svn st ' + ' temp/' + self.workspace
				outsvn = self.runCommand(cmdsvn)

				if debug:
					print('merge results: \n' + outsvn)

				# check conflicts in outsvn, 
				# Text conflicts: [0-9]; Tree conflicts: [0-9]
				regex = 'T[a-z]+\sconflicts:\s[0-9]+'
				matchs = re.findall(regex, outsvn)
				if len(matchs) == 0:
					pass
				else:
					for match in matchs:
						retConflicts += int(match.split(' ')[-1])

				if debug:
					print('conflicts: ' + str(retConflicts))

		return retConflicts

	def svnMerge(self):
		'''do subversion merge'''
		if debug:
			print('def svnMerge:\n')

		if self.go:
			if os.path.exists('temp/' + self.workspace):
				cmdsvn = 'svn merge --accept postpone ' + self.source + ' temp/' + self.workspace
				outsvn = self.runCommand(cmdsvn)

				if debug:
					print('svnMerge: ' + outsvn)

				if self.checkConflict() > 0:
					# create patch, put it into dest dir
					self.createPatch()
				else:
					# commit changes, identify revisions
					self.svnCommit()

	def createPatch(self):
		'''create patch when meet conflicts'''
		retpatch = False

		if debug:
			print('def createPatch:\n')

		if self.go:
			if os.path.exists('temp/' + self.workspace):
				f = open(self.output + '/automerge.patch', 'w+')

				revisions = self.getMergeRevisions()
				cmdsvn = 'svn diff temp/' + self.workspace
				outsvn = self.runCommand(cmdsvn)

				f.write(outsvn)
				f.close()

				if debug:
					print(cmdsvn)

			if os.path.exists(self.output + '/automerge.patch'):
				retpatch = True

		if debug:
			print(retpatch)

		return retpatch

	def svnCommit(self):
		'''commit workspace modifications'''
		retcommit = False

		if debug:
			print('def svnCommit:\n')

		if self.go:
			if os.path.exists('temp/' + self.workspace):
				revisions = self.getMergeRevisions()
				cmdsvn = "svn ci -m 'automerge: merged revisions " + revisions + \
				" from " + self.dest + "' temp/" + self.workspace
				outsvn = self.runCommand(cmdsvn)

				if debug:
					print(cmdsvn)
					print(outsvn)

				regex = 'Committed\srevision\s[0-9]+'
				match = re.search(regex, outsvn)

				if debug:
					print(match.group())
				if match:
					retcommit = True

		return retcommit

	def getMergeRevisions(self):
		'''check revisions been merged into workspace'''
		retrevisions = ''

		if debug:
			print('def getMergeRevisions:\n')

		if self.go:
			cmdsvn = "svn diff --depth empty " + " temp/" + self.workspace
			outsvn = self.runCommand(cmdsvn)

			if debug:
				print(outsvn)

			regex = 'Merged.*[0-9]+'
			match = re.search(regex, outsvn)

			if debug:
				print(match.group())

			if match:
				retrevisions = match.group().split(':')[-1]

		return retrevisions

	def getURLTail(self, url):
		'''
		given a url, return the last part of URL
		'''
		rettail = ''

		if url != '':
			url = url.rstrip('/')
			rettail = url.split('/')[-1]

		return rettail

	def runCommand(self, cmd):
		'''run string of command, return output'''
		retOut = ''
		if cmd != '':
			procsvn = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			retOut = procsvn.stdout.read()

		return retOut

	def goo(self):
		'''execute merge process'''
		if debug:
			print('def goo:\n')

		if self.help:
			self.usage()

		self.svnCheckout()
		self.svnMerge()

		print('Finished branch merge!')

	def usage(self):
		'''give help info'''
		print('''
merger: automatic merge one svn branch to another,
	if no conflicts, it will commit changes to subversion,
	if meet conflicts, it will create a patch.

	usage: merger.py source dest username passwd

	options:
	-s, --source	--- subversion source url to merge from
	-d, --dest		--- subversion dest url to merge to
	-u, --username	--- username for authenticate subversion
	-p, --passwd	--- passwd for authenticate subversion
	-h, --help		--- get help
			''')

	def validateSVNURL(self):
		'''check whether source and dest subversion path is visitable'''
		retvalidate = ''

		cmd = 'svn info ' + self.source
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		out = proc.stdout.read()
		if 'svn:' in out:
			retvalidate += ('Source URL:' + self.source + ' is invalid.\n')

		cmd = 'svn info ' + self.dest
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		out = proc.stdout.read()
		if 'svn:' in out:
			retvalidate += ('Destination URL:' + self.dest + ' is invalid.\n')

		return retvalidate

if __name__ == '__main__':
	merger = SVNMerger()

	validate = merger.validateSVNURL()
	if validate == '':
		merger.goo()
	else:
		print(validate)
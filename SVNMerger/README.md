SVNMerger
=========

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
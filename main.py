from git import *
import re
import time

import psycopg2
import redis

reponame = "reddit"

conn = psycopg2.connect(database="seminar", user="arno", password="seminar", host="127.0.0.1")
r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

repo = Repo(reponame)

def run():
	while r.scard("commitsToDo_" + reponame) > 0:
		commitHash = r.spop("commitsToDo_" + reponame)
		print(commitHash)
		r.sadd("commitsDone_" + reponame, commitHash)

		top = repo.commit(commitHash)

		parents = top.parents

		for par in parents:
			cmpRes = list(compareCommits(par, top))
			saveChangesToDb(cmpRes)

def buildQueue():
	cur = conn.cursor()
	cur.execute("delete from inserts where commit in (select id from commits where project = %s);", (reponame,))
	cur.execute("delete from deletes where deletingcommit in (select id from commits where project = %s);", (reponame,))
	cur.execute("delete from deletes where deletedcommit in (select id from commits where project = %s);", (reponame,))
	cur.execute("delete from commits where project = %s;", (reponame,))
	conn.commit()

    print("deleted old data from db")

	r.delete("commitsToDo_" + reponame)
	r.delete("commitsDone_" + reponame)

	commits = set()
	commitsDone = set()
	commits.add(repo.head.commit)

	while len(commits) > 0:
		com = commits.pop()
		commitsDone.add(com)
		r.sadd("commitsToDo_" + reponame, com.hexsha)
		saveCommitToDb(com, cur)

		for par in com.parents:
			if par not in commitsDone:
				commits.add(par)

        conn.commit()

def saveCommitToDb(commit, cur):
	query = "insert into commits (hexsha, author, date, project) select %s, %s, %s, %s where not exists (select id from commits where hexsha = %s and project = %s)"
	cur.execute(query, (commit.hexsha, commit.author.email, commit.authored_date, reponame, commit.hexsha, reponame))

def saveChangesToDb(cmpres):
	insertQuery = "insert into inserts (commit, filename, lineno) values (\
		(select id from commits where hexsha = %s),\
		%s,\
		%s)"

	deleteQuery = "insert into deletes (deletingcommit, deletedcommit, filename, lineno) values (\
		(select id from commits where hexsha = %s),\
		(select id from commits where hexsha = %s),\
		%s,\
		%s)"

	inserts = filter(lambda x: x['type'] == '+', cmpres)
	deletes = filter(lambda x: x['type'] == '-', cmpres)

	insertPars = map(lambda x: (x['commitHash'], x['fileName'], x['lineNo']), inserts)
	deletePars = map(lambda x: (x['deletingCommitHash'], x['deletedCommitHash'], x['fileName'], x['lineNo']), deletes)

	cur = conn.cursor()
	cur.executemany(insertQuery, insertPars)
	cur.executemany(deleteQuery, deletePars)
	conn.commit()

# what changes were made to get from com_a to com_b?
def compareCommits(com_a, com_b):
	errors = 0

	diffs = com_a.diff(com_b, create_patch=True, w=True) # w=True means whitespace is ignored

	rev = com_a.hexsha

	for diff in diffs:
		if diff.a_blob == None and diff.b_blob == None:
		    # not sure why this sometimes happens, ignore
		    continue

		# extract and parse the diff text
		difftxt = diff.diff
		difffile = (diff.a_blob or diff.b_blob).path

		parsedDiff = list(parseDiff(difftxt))

		# get blame info
		try:
			blame = repo.blame(rev, difffile, w=True)
			expBlame = list(expandBlame(blame))
		except:
			continue

		for line in parsedDiff:
			lineNo = line['line'] # lineNo is 1-indexed

			change = line['change']

			if change == '-':
				if(lineNo - 1 >= len(expBlame)):
					print("line number is " + str(lineNo) + "\nblame length is " + str(len(expBlame)) + "\nwhen comparing file " + difffile + " between revision " + com_a.hexsha + " and revision " + com_b.hexsha)
					raise Exception("blame wrong length")

				prevcommit = expBlame[lineNo - 1][0]
				author = prevcommit.author.email # author of the line that was just deleted

				res = {}
				res['type'] = "-"
				res['lineNo'] = lineNo
				res['deletingCommitHash'] = com_b.hexsha
				res['deletedCommitHash'] = prevcommit.hexsha
				res['fileName'] = difffile
				yield res
			else:
				res = {}
				res['type'] = "+"
				res['commitHash'] = com_b.hexsha
				res['fileName'] = difffile
				res['lineNo'] = lineNo
				yield res

# blame is a list [git.Commit, list: [<line>]]
# the result of this function is a list [git.Commit, line]
def expandBlame(blame):
	res = []

	for (com, lines) in blame:
		for l in lines:
			res.append((com, l))

	return res

# convert the text output of diff to a list of dictionaries containing changed lines
def parseDiff(diff):
	lines = diff.split('\n')

	# first two lines of diff are file paths, skip
	lines = lines[2:]

	i = 0
	while i < len(lines) - 1:
		line = lines[i]

		# next line is '@@ -123,10 +123,10 @@ ...'
		match = re.match(r'.* -([0-9]+),([0-9]+) \+([0-9]+),([0-9]+).*', line)

		if not match:
			print "no match: " + line
			i += 1
			continue

		a_start = int(match.group(1))
		a_len = int(match.group(2))

		b_start = int(match.group(3))
		b_len = int(match.group(4))

		a_at = a_start
		b_at = b_start

		while i < len(lines) - 1:
			i += 1

			line = lines[i]

			if len(line) == 0:
				continue

			if line[0] == '+':
				diffline = {}
				diffline['line'] = b_at
				diffline['change'] = line[0]
				diffline['txt'] = line[1:]

				b_at += 1

				yield diffline
			elif line[0] == '-':
				diffline = {}
				diffline['line'] = a_at
				diffline['change'] = line[0]
				diffline['txt'] = line[1:]

				a_at += 1

				yield diffline
			elif line[0] == ' ':
				a_at += 1
				b_at += 1
			elif line[0] == '@':
				i -= 1 # we went one too far
				break

		i += 1

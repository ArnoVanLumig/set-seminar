from git import *
import re
import time

import pickle

def run(commit):
	commitsToDo = set()
	commitsDone = set()

	commitsToDo.add(commit)

	while commitsToDo:
		top = commitsToDo.pop()
		parents = top.parents

		for par in parents:
			compareCommits(par, top)
			if par not in commitsDone:
				commitsToDo.add(par)

		commitsDone.add(top)

# what changes were made to get from com_a to com_b?
def compareCommits(com_a, com_b):
	errors = 0

	diffs = com_a.diff(com_b, create_patch=True)

	rev = com_a.hexsha
	#print(com_b.hexsha, com_a.hexsha)

	for diff in diffs:
		if diff.a_blob == None or diff.b_blob == None:
			# new file, ignore
			continue

		# extract and parse the diff text
		difftxt = diff.diff
		difffile = diff.b_blob.path

		#print(diff.b_blob.path, diff.a_blob.path)

		parsedDiff = list(parseDiff(difftxt))
		for x in parsedDiff:
			print(x)

		# get blame info
		blame = repo.blame(rev, difffile)
		expBlame = list(expandBlame(blame))

		for x in expBlame:
			print(x)

		#print("blame length at rev " + rev + " is: " + str(len(expBlame)) + " " + difffile)

		for line in parsedDiff:
			lineNo = line['line'] # lineNo is 1-indexed

			if(lineNo >= len(expBlame)):
				print("line number is " + str(lineNo) + "\nblame length is " + str(len(expBlame)))
				continue

			change = line['change']

			if change == '-':
				author = expBlame[lineNo - 1][0].author
				print("author %s deleted line %s in file %s that was originally by author %s" % (str(com_b.author), str(lineNo), str(difffile), str(author)))
			else:
				print("author %s added line %s in file %s" % (str(com_b.author), str(lineNo), str(difffile)))

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

start = time.time()
repo = Repo("~/Documents/5 1B/Seminar/testrepo")
latestCommit = repo.head.commit
#otherCommit = latestCommit.parents[0]
#compareCommits(latestCommit, otherCommit)
run(latestCommit)
end = time.time()

print(end - start)

# thediff = """--- a/drivers/python/rethinkdb/_import.py
# +++ b/drivers/python/rethinkdb/_import.py
# @@ -329,7 +329,6 @@ def read_json_array(json_data, file_in, callback, progress_info):

#              (obj, offset) = decoder.raw_decode(json_data, idx=offset)
#              callback(obj)
# -            progress_info[2].value += 1

#              # Read past whitespace to the next record
#              file_offset += offset
# @@ -374,7 +373,6 @@ def json_reader(task_queue, filename, db, table, primary_key, fields, progress_i
#              json_data = read_json_array(json_data[offset + 1:], file_in, callback, progress_info)
#          elif json_data[offset] == "{":
#              json_data = read_json_single_object(json_data[offset:], file_in, callback)
# -            progress_info[2].value = 1
#          else:
#              raise RuntimeError("Error: JSON format not recognized - file does not begin with an object or array")

# @@ -428,7 +426,6 @@ def csv_reader(task_queue, filename, db, table, primary_key, options, progress_i
#                  if len(obj[key]) == 0:
#                      del obj[key]
#              object_callback(obj, db, table, task_queue, object_buffers, buffer_sizes, options["fields"], exit_event)
# -            progress_info[2].value += 1

#      if len(object_buffers) > 0:
#          task_queue.put((db, table, object_buffers))
# @@ -490,7 +487,7 @@ def print_progress(ratio):

#  def update_progress(progress_info):
#      lowest_completion = 1.0
# -    for (current, max_count, rows) in progress_info:
# +    for (current, max_count) in progress_info:
#          curr_val = current.value
#          max_val = max_count.value
#          if curr_val < 0:
# @@ -529,9 +526,8 @@ def spawn_import_clients(options, files_info):
#              client_procs[-1].start()

#          for file_info in files_info:
# -            progress_info.append((multiprocessing.Value(ctypes.c_longlong, -1), # Current lines/bytes processed
# -                                  multiprocessing.Value(ctypes.c_longlong, 0), # Total lines/bytes to process
# -                                  multiprocessing.Value(ctypes.c_longlong, 0))) # Total rows processed
# +            progress_info.append((multiprocessing.Value(ctypes.c_longlong, -1),
# +                                  multiprocessing.Value(ctypes.c_longlong, 0)))
#              reader_procs.append(multiprocessing.Process(target=table_reader,
#                                                          args=(options,
#                                                                file_info,
# @@ -564,12 +560,7 @@ def spawn_import_clients(options, files_info):
#              print_progress(1.0)

#          # Continue past the progress output line
# -        def plural(num, text):
# -            return "%d %s%s" % (num, text, "" if num == 1 else "s")
# -
#          print ""
# -        print "%s imported in %s" % (plural(sum([info[2].value for info in progress_info]), "row"),
# -                                       plural(len(files_info), "table"))
#      finally:
#          signal.signal(signal.SIGINT, signal.SIG_DFL)
# """

# for d in parseDiff(thediff):
# 	print(d)
import psycopg2

reponame = "rethinkdb"

filenameBlacklist = ["railties/doc/guides%%", "guides/%%", "%%jquery%%js", "%%CHANGELOG%%", "%%README%%", "%%COPYING%%", "%%LICENCE%%", "lib/%%", "external/%%", "bench/workloads/baseline/baseline-git/bench/stress-client/sqlite3.c", "admin/static/js%%", "bench/serializer-bench/lab_journal%%"]
blacklistQuery = "and".join(map(lambda x: " filename not like '%s' " % x, filenameBlacklist))

query = "select c1.author as deletingAuthor, c2.author as deletedAuthor, count(deletes.id) as count from deletes \
inner join commits as c1 on deletes.deletedcommit = c1.id \
inner join commits as c2 on deletes.deletingcommit = c2.id \
where c2.project = %s and " + blacklistQuery + " \
group by c1.author, c2.author \
having count(deletes.id) > 10 \
order by count desc;"

conn = psycopg2.connect(database="seminar", user="arno", password="seminar", host="127.0.0.1")

cur = conn.cursor()
cur.execute(query, (reponame,))
res = cur.fetchall()

authors = set()
for r in res:
	authors.add(r[0])
	authors.add(r[1])
authors = list(authors)

authorsDict = {}
for r in res:
	if r[0] not in authorsDict:
		authorsDict[r[0]] = 0
	if r[1] not in authorsDict:
		authorsDict[r[1]] = 0
	authorsDict[r[0]] += r[2]
	authorsDict[r[1]] += r[2]

authors.sort(key=lambda a: authorsDict[a], reverse=True)

matrix = [ [0 for y in range(len(authors))] for x in range(len(authors))]

for r in res:
	a1 = authors.index(r[0])
	a2 = authors.index(r[1])

	matrix[a1][a2] = r[2]

print(";" + ";".join(authors))
i = 0
for row in matrix:
	rowstr = map(lambda x: str(x) if x > 0 else "", row)
	print(authors[i] + ";" + ";".join(rowstr))
	i += 1
import psycopg2
from collections import Counter

reponame = "rethinkdb"

filenameBlacklist = ["railties/doc/guides%%", "guides/%%", "%%jquery%%js", "%%CHANGELOG%%", "%%README%%", "%%COPYING%%", "%%LICENCE%%", "lib/%%", "external/%%", "bench/workloads/baseline/baseline-git/bench/stress-client/sqlite3.c", "admin/static/js%%", "bench/serializer-bench/lab_journal%%"]
blacklistQuery = "and".join(map(lambda x: " filename not like '%s' " % x, filenameBlacklist))

query = "select c1.date - c2.date from deletes \
inner join commits as c1 on deletes.deletingcommit = c1.id \
inner join commits as c2 on deletes.deletedcommit = c2.id \
where c2.project = %s and " + blacklistQuery + ";"

conn = psycopg2.connect(database="seminar", user="arno", password="seminar", host="127.0.0.1")

cur = conn.cursor()
cur.execute(query, (reponame,))
res = cur.fetchall()

c = Counter()
for r in res:
	c[r] += 1

for (i,) in c.elements():
	print(i)
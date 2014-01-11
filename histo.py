import psycopg2
from collections import Counter

reponame = "rethinkdb"

query = "select c1.date - c2.date from deletes \
inner join commits as c1 on deletes.deletingcommit = c1.id \
inner join commits as c2 on deletes.deletedcommit = c2.id where c2.project = %s;"

conn = psycopg2.connect(database="seminar", user="arno", password="seminar", host="127.0.0.1")

cur = conn.cursor()
cur.execute(query, (reponame,))
res = cur.fetchall()

c = Counter()
for r in res:
	c[r] += 1

for (i,) in c.elements():
	print(i)
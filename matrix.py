import psycopg2

query = "select c1.author as deletingAuthor, c2.author as deletedAuthor, count(deletes.id) as count from deletes \
inner join commits as c1 on deletes.deletingcommit = c1.id \
inner join commits as c2 on deletes.deletedcommit = c2.id \
group by c1.author, c2.author \
having count(deletes.id) > 10 \
order by count desc;"

conn = psycopg2.connect(database="seminar", user="arno", password="seminar", host="127.0.0.1")

cur = conn.cursor()
cur.execute(query)
res = cur.fetchall()

authors = set()
for r in res:
	authors.add(r[0])
	authors.add(r[1])
authors = list(authors)

matrix = [ [0 for y in range(len(authors))] for x in range(len(authors))]

for r in res:
	a1 = authors.index(r[0])
	a2 = authors.index(r[1])

	matrix[a1][a2] = r[2]

print(";" + ";".join(authors))
i = 0
for row in matrix:
	rowstr = map(lambda x: str(x), row)
	print(authors[i] + ";" + ";".join(rowstr))
	i += 1
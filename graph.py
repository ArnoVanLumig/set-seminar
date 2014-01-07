import psycopg2
import json

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

authorsDict = {}
for r in res:
	if r[0] not in authorsDict:
		authorsDict[r[0]] = 0
	if r[1] not in authorsDict:
		authorsDict[r[1]] = 0
	authorsDict[r[0]] += r[2]
	authorsDict[r[1]] += r[2]

authors.sort(key=lambda a: authorsDict[a], reverse=True)

jsonRes = {}
jsonRes['nodes'] = map(lambda x: {"name": x}, authors) # put in dictionaries

links = []
for a1 in range(len(authors)):
	for a2 in range(a1):
		auth1 = authors[a1]
		auth2 = authors[a2]

		cnt = 0
		for r in res:
			if (r[0] == auth1 and r[1] == auth2) or (r[1] == auth1 and r[0] == auth2):
				cnt += r[2]

		if cnt < 1000:
			continue

		link = {}
		link['source'] = a1
		link['target'] = a2
		link['value'] = cnt
		links.append(link)
jsonRes['links'] = links

print json.dumps(jsonRes, indent=4)
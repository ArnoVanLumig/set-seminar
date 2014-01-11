import psycopg2
import json

reponame = "rails"

query = "select c1.author as deletingAuthor, c2.author as deletedAuthor, count(deletes.id) as count from deletes \
inner join commits as c1 on deletes.deletingcommit = c1.id \
inner join commits as c2 on deletes.deletedcommit = c2.id where c2.project = %s \
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

filteredAuthors = set()

links = []
for a1 in range(len(authors)):
	for a2 in range(a1):
		auth1 = authors[a1]
		auth2 = authors[a2]

		cnt = 0
		for r in res:
			if (r[0] == auth1 and r[1] == auth2) or (r[1] == auth1 and r[0] == auth2):
				cnt += r[2]

		if cnt < 300:
			continue

		link = {}
		link['source'] = auth1
		link['target'] = auth2
		link['value'] = cnt
		links.append(link)

		filteredAuthors.add(auth1)
		filteredAuthors.add(auth2)

filteredAuthors = list(filteredAuthors)
filteredAuthors.sort(key=lambda a: authorsDict[a], reverse=True)

jsonLinks = []
for link in links:
	lnk = {}
	lnk['source'] = filteredAuthors.index(link['source'])
	lnk['target'] = filteredAuthors.index(link['target'])
	lnk['value'] = link['value']

	jsonLinks.append(lnk)

jsonRes = {}
jsonRes['nodes'] = map(lambda x: {"name": x}, filteredAuthors) # put in dictionaries
jsonRes['links'] = jsonLinks

print json.dumps(jsonRes, indent=4)
from git import *

reponame = "rails_ram"

repo = Repo(reponame)

commitqueue = set([repo.head.commit])
commitsDone = set()

nameMap = {} # map author name to set of email addresses

while commitqueue:
	head = commitqueue.pop()
        commitsDone.add(head)
        print(len(commitsDone))

	for par in head.parents:
            if par not in commitsDone:
		commitqueue.add(par)

	if head.author.name not in nameMap:
		nameMap[head.author.name] = set()

	nameMap[head.author.name].add(head.author.email)

mailMap = {}

for k in nameMap:
	vs = nameMap[k]
	for v in vs:
		if v not in mailMap:
			mailMap[v] = set()

		mailMap[v].add(k)

# data extraction done, now find the clusters

identities = [] # [([email], [name])]

for em in mailMap:
	identities.append(([em], list(mailMap[em])))

def mergeIds(id1, id2):
	mails = [ n for n in id1[0] ] + [ n for n in id2[0] ]
	names = [ n for n in id1[1] ] + [ n for n in id2[1] ]
	return (list(set(mails)), list(set(names)))

change = True
while change:
	change = False

	merge1, merge2 = None, None

	for i1 in range(len(identities)):
		for i2 in range(len(identities)):
			if i1 == i2:
				continue

			ident1 = identities[i1]
			ident2 = identities[i2]

			for name in ident1[1]:
				if name in ident2[1]:
					change = True
					break
			for email in ident1[0]:
				if change or email in ident2[0]:
					change = True
					break

			if change:
				merge1, merge2 = i1, i2
				break

			i2 += 1
		if change:
			break

		i1 += 1

	if change:
		mergeId1 = identities[merge1]
		mergeId2 = identities[merge2]

		identities.pop(max(merge1, merge2))
		identities.pop(min(merge1, merge2))

		identities.append(mergeIds(mergeId1, mergeId2))

for ident in identities:
    if len(ident[0]) > 1:
		print ident

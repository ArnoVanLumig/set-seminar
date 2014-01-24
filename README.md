SET Seminar
===========

This repository contains some scripts that can be used to explore Git repositories. The scripts are not indended for any production use.

For the license see the LICENSE file in this repository.

Installation
============

These are the steps to get from an "empty" server to a force-directed graph based on a real repository. The steps you have to take for matrix.py and histo.py are basically the same except the last 4 steps.

0. Install python2, psycopg2, postgresql, redis, the redis python driver. Both psycopg2 and redis and psycopg2 can be installed with pip. Clone the set-seminar repository.
1. Create database and database tables (see query below). Update the database credentials that are used in all *.py files.
2. Clone a git repository into directory "foo" (see "Directory layout")
3. Edit set-seminar/main.py and graph.py to have "reponame = 'foo'"
4. Run "python2 -i set-seminar/main.py" and call "buildQueue()" from the REPL. This can take a while on large repositories
5. As many times as you like concurrently: run "python2 -i set-seminar/main.py" and call "run()" in the REPL. This can also take quite some time on large repos (a few hours for Rails on my server).
6. When this is done you should have the change data in your Postgresql database
7. Edit set-seminar/graph.py to have "reponame = 'foo'"
8. Edit the blacklist of set-seminar/graph.py to taste (see "file blacklisting query"). You can use a percent sign (actually two because they need to be escaped) as a wildcard.
9. Run "python2 set-seminar/graph.py > graph.json". This takes a few minutes.
10. Run "python2 -m SimpleHTTPServer 8080" in the directory that contains graph.json
11. point your browser to "http://localhost:8080/graph.html". Adjust the parameters in graph.html to taste until the visualisation looks decent.

Directory layout
================

This is the directory layout that you should use to run the scripts. Of course, the names of the directories are just examples and can be changed. In the steps of the instructions above I assume that your current directory is "/some_folder".

/some_folder
    /foo
        this is the directory of the repository under investigation
    /set-seminar
        main.py
        graph.py
        graph.html
        matrix.py
        histo.py
        ...

Database creation queries
=========================

There are three tables in the database: commits, inserts and deletes. The inserts and deletes are all linked by a foreign key to a commit. A commit record has a "project" property that is equal to the directory name of the repository ("foo" in the example above).

The database may benefit from some more normalisation, but this is not implemented yet and not a priority.

The queries below are untested.

    create table commits
    (
        id serial primary key,
        hexsha varchar(40) not null,
        author varchar(200) not null,
        date integer not null,
        project varchar(20) not null
    );

    create index on commits (hexsha);
    create index on commits (project);

    create table inserts
    (
        id serial primary key,
        commit integer not null references commits (id),
        filename varchar(1000) not null,
        lineno integer not null
    );

    create index on inserts (commit);
    create index on inserts (filename);

    create table deletes
    (
        id serial primary key,
        deletingcommit integer not null references commits (id),
        deletedcommit integer not null references commits (id),
        filename varchar(1000) not null,
        lineno integer not null
    );

    create index on deletes (deletingcommit);
    create index on deletes (deletedcommit);
    create index on deletes (filename);

File blacklisting query
=======================

The below query produces a sorted list of the most-edited files with their edit count. This is useful for detecting files that should be blacklisted.

  select filename, count(deletes.id) from deletes
  inner join commits as c1 on c1.id = deletes.deletedcommit
  where project = 'foo'
  group by filename
  order by count desc;
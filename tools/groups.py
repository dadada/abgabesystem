#!/bin/python

from sys import argv
from subprocess import run
from os import chdir
from os.path import isdir

course_url = argv[1]

with open(argv[2], 'r', encoding="latin-1") as csv:
    for line in csv:
        tokens = line.split(';')
        student = tokens[5].replace('"', "").split(" ")[0]
        group = tokens[0].replace('"', "").split(" ")[0]
        if group != argv[3]:
            continue
        url = course_url + "/solutions/" + student + "/solutions"
        path = "solutions/" + group + "/" + student
        if isdir(path):
            chdir(path)
            run(["git", "pull"])
            chdir("../../..")
        else:
            run(["git", "clone", url, path])

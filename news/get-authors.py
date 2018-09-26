#!/usr/bin/env python3

from subprocess import check_output

last_tag = check_output(["git", "describe", "--abbrev=0"], universal_newlines=True)
authors = {}
log_range = last_tag.strip() + "..HEAD"
output = check_output(["git", "log", log_range, "--format=%ae\t%an"], universal_newlines=True)
for line in output.splitlines():
    email, fullname = line.split("\t")
    email = email.split("@")[0].replace(".", "")
    if email in authors:
        continue
    authors[email] = fullname

for nick, fullname in authors.items():
    with open("{}.author".format(nick), "w") as f:
        f.write(fullname)
        f.write("\n")

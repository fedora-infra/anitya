#!/usr/bin/env python3

"""
This script is browsing through git commit history (starting at latest tag),
collects all authors of commits and creates fragment for `towncrier`_ python module.

It's meant to be run before creating a final documentation before new release.

Example:
    $ python get_authors.py

.. _towncrier:
   https://github.com/hawkowl/towncrier

(c) 2018 - Copyright Red Hat Inc

Authors:
    Aurelien Bompard
    Michal Konecny
"""


from subprocess import check_output

last_tag = check_output(["git", "describe", "--abbrev=0"], universal_newlines=True)
authors = {}
log_range = last_tag.strip() + "..HEAD"
output = check_output(
    ["git", "log", log_range, "--format=%ae\t%an"], universal_newlines=True
)
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

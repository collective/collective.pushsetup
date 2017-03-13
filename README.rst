pushsetup
=========
Dump the entire state of a Plone site using Generic Setup

Setup
-----
Create local repostiory as proxy to destination repository. 'Origin' remote repository

Usage
-----
    usage: bin/instance run <path-to-pushsetup.py> [--site SITE] [--user USER] repository

    Acquire Plone site's Generic Setup state and push it to git repository via
    local proxy repository.

    positional arguments:
      repo         Path to local proxy git repository to extract site's state to.  Push changes to its origin.

    optional arguments:
      -h, --help   show this help message and exit
      --site SITE  Name of site whose state to push (default: Plone)
      --user USER  Username to acquire Generic Setup of site (default: admin)
      -c C         Do not use (required by Zope when executing this scipt)
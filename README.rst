pushsetup
=========
Dump the entire state of a Plone site using Generic Setup

Setup
-----
1. Create local repostiory as proxy to destination repository
2. Configure settings (by now in src/collective/pushsetup/pushsetup.py)

   1. PLONE_SITE: Name of plone site to acquire state from
   2. PLONE_USER: User to be used for state aquisition
   3. REPO_PATH: Path to local repository created in step 1

Execution
---------
Run `bin/instance run <path-to-pushsetup.py>` to put all Generic Setup files
into the local repository, commit and push to origin repository.

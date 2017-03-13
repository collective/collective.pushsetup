import argparse
import tarfile
import sys
import logging
import git
import StringIO
import os


from AccessControl.SecurityManagement import newSecurityManager
from Testing import makerequest
from zope.component.hooks import setSite


def getSite(app, site_id, admin_id):
    app = makerequest.makerequest(app)
    admin = app.acl_users.getUser(admin_id)
    if admin is None:
        admin = app[site_id].acl_users.getUser(admin_id)
    admin = admin.__of__(app[site_id].acl_users)
    newSecurityManager(None, admin)

    site = app.get(site_id, None)

    if site is None:
        print "'%s' not found (maybe a typo?)." % site_id
        print "To create a site call 'import_structure' first."
        raise ValueError

    setSite(site)  # enable lookup of local components

    return site


def getLogger(logfilename='var/log/pushsetup.log'):
    logger = logging.getLogger('pushsetup')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(logfilename)
    fh.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(file_formatter)
    # add the handlers to the logger
    logger.addHandler(fh)

    return logger


def makeArgParser():
    parser = argparse.ArgumentParser(usage='bin/instance run <path-to-pushsetup.py> '
                                           '[--site SITE] [--user USER] repository',
                                     description='Acquire Plone site\'s Generic Setup state and push it '
                                                 'to git repository via local proxy repository')

    parser.add_argument('--site', dest='site', default='Plone',
                        help='Name of site whose state to push (default: Plone)')
    parser.add_argument('--user', dest='user', default='admin',
                        help='Username to acquire Generic Setup of site (default: admin)')
    parser.add_argument('repo',
                        help='Path to local proxy git repository to extract site\'s state to. '
                             'Push changes to its origin.')

    parser.add_argument('-c', default='',
                        help='Do not use (required by Zope when executing this scipt)')

    return parser


def main(app):
    logger = getLogger()

    parser = makeArgParser()
    args = parser.parse_args()

    site = getSite(app, args.site, args.user)
    stool = site.portal_setup

    logger.info("Acquiring Generic Setup state from site '%s' using user '%s'", args.site, args.user)

    result = stool.runAllExportSteps()
    tarball = StringIO.StringIO(result['tarball'])

    logger.info('Checkout master branch of local repository and get origin repository')

    # enable user's home directory shortcut
    args.repo = os.path.expanduser(args.repo)

    try:
        # access repository (master branch)
        repository = git.Repo(args.repo)
        repository.git.checkout('master')
        remote = repository.remote('origin')
    except (git.InvalidGitRepositoryError, git.NoSuchPathError, git.GitCommandError, ValueError) as e:
        logger.exception('Failed accessing local git repository')
        sys.exit(1)

    try:
        # abort if local repository is not clean
        if repository.head.commit.diff(None) != []:
            logger.error('Found uncommitted changes to local repository. Expecting clean master branch')
            sys.exit(1)
    except git.GitCommandError as e:
        logger.exception('Failed checking for uncommitted local changes')
        sys.exit(1)

    try:
        # pull remote prepository in case it changed
        changes = remote.pull()
        assert len(changes) == 1

        if (changes[0].flags & git.FetchInfo.HEAD_UPTODATE) != 0:
            logger.info('Local repository is up-to-date')
        else:
            logger.info('Pulled changes from remote repository')
    except git.GitCommandError as e:
        logger.exception('Failed pulling from remote repository')
        sys.exit(1)

    logger.info("Extracting state to local repository '%s'", args.repo)

    try:
        # extract dump into repository
        with tarfile.open(fileobj=tarball, errorlevel=2) as archive:
            # The directory should already exist as we already opened the contained git repository.
            # TODO: check for paths in archive that escape the repository's directory
            archive.extractall(args.repo)
    except tarfile.TarError as e:
        logger.exception('Failed extracting state to local repository')
        sys.exit(1)

    logger.info("Commiting changes to local repository '%s'", args.repo)

    try:
        # commit all changes to local repository
        repository.git.add('--all')
        repository.git.commit('--allow-empty', '-m', 'update config dump')
    except git.GitCommandError as e:
        logger.exception('Failed commiting changes to local repository')
        sys.exit(1)

    logger.info("Pushing changes to remote repository '%s'", remote.name)

    try:
        # push commit from local to remote repository
        remote.push()
    except git.GitCommandError as e:
        logger.exception('Failed pushing changes to remote repository')
        sys.exit(1)

    print "Pushed Plone state to remote repository"


if "app" in locals():
    main(app)

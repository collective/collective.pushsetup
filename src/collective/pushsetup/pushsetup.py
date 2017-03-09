import argparse
import tarfile
import git
import StringIO

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


def makeArgParser():
    parser = argparse.ArgumentParser(description='Acquire Plone site\'s Generic Setup state and push it '
                                                 'to git repository via local proxy repository.'
                                                 'Usage: bin/instance run <path-to-pushsetup.py> [args]')

    parser.add_argument('--site', '-s', dest='site', default='Plone',
                        help='Name of site whose state to push (default: Plone)')
    parser.add_argument('--user', '-u', dest='user', default='admin',
                        help='Username to acquire Generic Setup of site (default: admin)')
    parser.add_argument('--local-repo', '-r', dest='repo',
                        help='Proxy git repository to extract site\'s state to. Then pushed to origin.')

    parser.add_argument('-c', default='',
                        help='Do not use (required by Zope when executing this scipt)')

    return parser


def main(app):
    try:
        parser = makeArgParser()
        args = parser.parse_args()

        site = getSite(app, args.site, args.user)
        stool = site.portal_setup

        result = stool.runAllExportSteps()
        tarball = StringIO.StringIO(result['tarball'])

        # access repository (master branch)
        repository = git.Repo(args.repo)
        repository.git.checkout('master')

        # extract dump into repository
        with tarfile.open(fileobj=tarball, errorlevel=2) as archive:
            archive.extractall(args.repo)

        # commit all changes to local repository
        repository.git.add('--all')
        repository.git.commit('-m', 'update config dump')

        # push commit to remote repository
        repository.remotes['origin'].push()

    except Exception:
        print "Failed to push Plone state to repository"
        raise

    print "Pushed Plone state to repository"


if "app" in locals():
    main(app)

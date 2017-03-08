import tarfile
import git

from Products.GenericSetup.interfaces import ISetupTool
from zope.component import queryUtility
from AccessControl.SecurityManagement import newSecurityManager
from Testing import makerequest
from zope.component.hooks import setSite


REPO_PATH = "~/config/"
PLONE_USER = "bernp"
PLONE_SITE = "pcp"


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


def main(app):
    try:
        site = getSite(app, PLONE_SITE, PLONE_USER)
        stool = queryUtility(ISetupTool)

        result = stool.runAllExportSteps()
        tarball = result['tarball']

        # access repository (master branch)
        repository = git.Repo(REPO_PATH)
        repository.git.checkout('master')

        # extract dump into repository
        with tarfile.open(fileobj=tarball, errorlevel=2) as archive:
            archive.extractall(REPO_PATH)

        # commit all changes to local repository
        repository.git.commit('-a', '-m', 'update config dump')

        # push commit to remote repository
        repository.remotes['origin'].push()

    except Exception:
        print "Failed to push Plone state to repository"
        raise

    print "Pushed Plone state to repository"


if "app" in locals():
    main(app)

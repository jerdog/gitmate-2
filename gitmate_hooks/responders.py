"""
This module contains basic functions to create, update and delete entries from
a database. The current scope of this module does not require testing as it is
only basic operations on Django models.
"""
import logging
from typing import List

from celery.schedules import crontab
from django.contrib.auth.models import User
from IGitt.Interfaces.Actions import InstallationActions
from IGitt.Interfaces.Installation import Installation as IGittInstallation
from IGitt.Interfaces.Repository import Repository as IGittRepository
from IGitt.Interfaces.User import User as IGittUser

from gitmate_config.enums import Providers
from gitmate_config.models import Installation
from gitmate_config.models import Repository
from gitmate_config.utils import get_user_if_exists
from gitmate_config.views import RepositoryViewSet
from gitmate_hooks.utils import ResponderRegistrar


@ResponderRegistrar.responder(
    'hooks',
    InstallationActions.CREATED,
    InstallationActions.REPOSITORIES_ADDED
)
def update_installed_repositories(
        installation: IGittInstallation,
        sender: IGittUser,
        repos: List[IGittRepository]
):
    """
    Creates and updates an installation object in the database.
    """
    db_installation, _ = Installation.objects.get_or_create(
        provider=installation.hoster, identifier=installation.identifier)

    # add user to installation administrators
    db_user = get_user_if_exists(sender)
    if db_user:
        db_installation.admins.add(db_user)
        db_installation.save()

    for repo in repos:
        Repository.objects.update_or_create(
            identifier=repo.identifier,
            provider=repo.hoster,
            defaults={
                'identifier': repo.identifier,
                'full_name': repo.full_name,
                'installation': db_installation,
                'active': True
            }
        )


@ResponderRegistrar.responder('hooks', InstallationActions.DELETED)
def delete_installation(installation: IGittInstallation, _: IGittUser):
    """
    Deletes an installation object from the database.
    """
    Installation.from_igitt_installation(installation).delete()


@ResponderRegistrar.responder(
    'hooks', InstallationActions.REPOSITORIES_REMOVED)
def remove_installed_repositories(
        installation: IGittInstallation,
        sender: IGittUser,
        repos: [IGittRepository]
):
    """
    Removes repositories from an existing installation.
    """

    # add user to installation administrators
    db_user = get_user_if_exists(sender)
    if db_user:
        db_inst = Installation.from_igitt_installation(installation)
        db_inst.admins.add(db_user)
        db_inst.save()

    for repo in repos:
        db_repo = Repository.from_igitt_repo(repo)
        db_repo.installation = None
        db_repo.save()


@ResponderRegistrar.scheduler(crontab('0', '0', '*', '*', '*'))
def remove_non_existent_repos():
    """
    Checks all repositories every 24 hours, and if they are deleted, delete
    from database as well.
    """
    for user in User.objects.all():
        for provider in Providers:
            if provider == Providers.GITHUB_APP:
                continue
            RepositoryViewSet.unlink_repos_for_provider(
                user=user, provider=provider)

    for repo in Repository.objects.all().exclude(
            provider=Providers.GITHUB_APP.value):
        try:
            repo.igitt_repo.refresh()
        except RuntimeError as error:
            if error.args[-1] == 404:
                logging.info(f'Deleting repository {repo}')
                repo.delete()
            else:  # pragma: no cover, for logging
                logging.error(f'Cannot refresh data on {repo.igitt_repo}')

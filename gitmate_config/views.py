from IGitt.GitHub import GH_INSTANCE_URL
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from rest_framework import mixins
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from social_django.models import UserSocialAuth

from gitmate.apps import get_all_plugins
from gitmate.utils import get_webhook_url
from gitmate_config.enums import Providers
from gitmate_config.models import Installation
from gitmate_config.models import Organization
from gitmate_config.models import Repository
from gitmate_config.utils import GitMateUser

from .serializers import PluginSettingsSerializer
from .serializers import RepositorySerializer
from .serializers import UserSerializer
from .utils import divert_access_to_orgs
from .utils import divert_access_to_repos


class RepositoryViewSet(
        GenericViewSet,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
):
    """
    Manages the repositories owned by the authenticated user.

    list:
    Returns a list of all repositories owned by the authenticated user.

    retrieve:
    Returns a specified repository of the authenticated user.

    partial_update:
    Patches a specified repository of the authenticated user.
    """
    serializer_class = RepositorySerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return RepositoryViewSet.get_queryset_for_user(self.request.user)

    @staticmethod
    def get_queryset_for_user(user):
        repos = Repository.objects.filter(admins__in=[user])
        for i in Installation.objects.filter(admins__in=[user]):
            repos |= i.repos.all()
        return repos.order_by('-active', 'full_name')

    @staticmethod
    def unlink_repos_for_provider(user, provider, repos=None, repo_ids=None):
        gitmate_user = GitMateUser(user)
        repos = repos if repos else gitmate_user.master_repos(provider)
        repo_ids = repo_ids if repo_ids else [repo.identifier
                                              for repo in repos]
        # unlink the repositories in the provider for which the
        # user no longer has access to, excluding installation
        # repositories
        inaccessible_repos = RepositoryViewSet.get_queryset_for_user(
            user).filter(
                provider=provider.value).exclude(
                    Q(identifier__in=repo_ids) |
                    Q(installation__isnull=False))

        # delete them if he's the only administrator
        inaccessible_repos.annotate(
            num_admins=Count('admins')
        ).filter(num_admins=1).delete()

        # give the access to someone else otherwise
        divert_access_to_repos(inaccessible_repos, user)

    @staticmethod
    def AddAdminToOrg(repo, igitt_repo, provider, request, checked_orgs):

        igitt_org = igitt_repo.top_level_org

        org, created = Organization.objects.get_or_create(
            name=igitt_org.name,
            provider=provider.value,
            defaults={'primary_user': request.user})

        if created or (
            org.name not in checked_orgs
            and request.user not in org.admins.all()
        ):
            masters = {m.identifier for m in igitt_org.masters}
            for admin in repo.admins.all():
                if admin.social_auth.get(
                        provider=repo.provider
                ).extra_data['id'] in masters:
                    org.admins.add(admin)

            if created:
                # The user who first lists a repo will also be
                # able to manage the org as he's the only one
                org.admins.add(request.user)
                org.save()

            checked_orgs.add(org.name)
        return igitt_org, checked_orgs


    @staticmethod
    def UpdateOrCreateRepo(igitt_repo, provider, request):
        # Orgs already checked for master access of the current user
        checked_orgs = set()

        repo, created = Repository.objects.get_or_create(
            identifier=igitt_repo.identifier,
            provider=provider.value,
            defaults={'active': False,
                      'user': request.user,
                      'full_name': igitt_repo.full_name,
                      'identifier': igitt_repo.identifier})
        repo.admins.add(request.user)

        if not created:
            repo.full_name = igitt_repo.full_name

        if repo.org is None:
            igitt_org, checked_orgs = RepositoryViewSet.AddAdminToOrg(repo, igitt_repo, provider, request, checked_orgs)
        return repo, checked_orgs

    def list(self, request):
        if int(request.GET.get('cached', '1')) > 0:
            return super().list(request)

        gitmate_user = GitMateUser(request.user)

        for provider in Providers:
            try:
                master_repos = gitmate_user.master_repos(provider)
                repo_ids = [repo.identifier for repo in master_repos]

                for igitt_repo in master_repos:
                    repo = self.UpdateOrCreateRepo(igitt_repo, provider, request)
                    repo.save()

                RepositoryViewSet.unlink_repos_for_provider(
                    user=request.user, provider=provider, repos=master_repos,
                    repo_ids=repo_ids)

                # TODO: validate if a cached repo was removed. Handling if it
                # was active?
            except (UserSocialAuth.DoesNotExist, KeyError):  # pragma: no cover
                # User never gave us his key for that provider, or the provider
                # isn't relevant to natural fetch process. e.g. `github-app`
                pass

        return super().list(request)

    def update(self, request, *args, **kwargs):
        """
        Updates the repository. This will be called by `super` on both
        partial and full update (PATCH and PUT), only the `active` property
        is writable (see serializer) so this takes care of
        activation/decativation of the webhook only.
        """
        instance = self.get_object()
        if instance.installation is not None:
            # github app should configure installations from GitHub web UI
            url = (f'{GH_INSTANCE_URL.rstrip("/")}/settings/installations/'
                   f'{instance.installation.identifier}')
            return Response({
                'msg': f'Please visit {url} to configure your installation.'
            }, status.HTTP_406_NOT_ACCEPTABLE)

        active_changed = (request.data['active'] != instance.active
                          if 'active' in request.data
                          else False)

        retval = super().update(request, *args, **kwargs)

        if active_changed:
            instance = self.get_object()
            repo = instance.igitt_repo
            hook_url = get_webhook_url(instance.provider)
            if instance.active:
                # increment the repository activation count
                instance.activation_count += 1
                instance.save()

                # turn on default plugins for the first time only
                if instance.activation_count == 1:
                    plugins = [{'name': conf.plugin_name, 'active': True}
                               for conf in get_all_plugins(default_only=True)]
                    instance.settings = plugins

                # register the webhook for repository events
                repo.register_hook(hook_url, settings.WEBHOOK_SECRET)
            else:
                repo.delete_hook(hook_url)

        return retval


class UserViewSet(
        GenericViewSet,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        mixins.DestroyModelMixin
):
    """
    Manages the users within GitMate.

    retrieve:
    Returns the user details of the authenticated user.

    destroy:
    Deletes the user account of the authenticated user.

    update:
    Updates the user details of the authenticated user.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_object(self):
        if self.kwargs.get('pk') in ['me', self.request.user.pk]:
            return self.request.user
        raise PermissionDenied

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        # Scan for user repos. If they have multiple admins, make someone else
        # the operating user and then remove the user.
        divert_access_to_repos(user.repository_set.all(), user)

        # Scan for user maintained orgs. If they have multiple admins, make
        # someone else the maintainer and then remove the user.
        divert_access_to_orgs(user.orgs.all(), user)

        return super().destroy(request, *args, **kwargs)


class PluginSettingsViewSet(
        GenericViewSet,
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        mixins.UpdateModelMixin
):
    """
    Manages the configuration for plugins of each repository.

    retrieve:
    Retrieves the configuration for the plugins of a repository.

    list:
    Retrieves the list of configurations for the plugins of all repositories
    owned by the authenticated user.

    update:
    Updates the configuration for the plugins of a repository.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = PluginSettingsSerializer

    def get_queryset(self):
        return [repo.get_plugin_settings_with_info(self.request)
                for repo in Repository.objects.filter(user=self.request.user)]

    def get_object(self):
        repo = get_object_or_404(Repository, pk=self.kwargs.get('pk'))
        if ((repo.installation and
             self.request.user not in repo.installation.admins.all()) or
                (self.request.user not in repo.admins.all())):
            raise PermissionDenied
        return repo

    def retrieve(self, request, *args, **kwargs):
        repo = self.get_object()
        serializer = PluginSettingsSerializer(
            instance=repo.get_plugin_settings_with_info(request))
        return Response(serializer.data, status.HTTP_200_OK)

    def update(self, request, pk=None, *args, **kwargs):
        repo = self.get_object()
        repo.settings = request.data
        serializer = PluginSettingsSerializer(
            instance=repo.get_plugin_settings_with_info(request))
        return Response(serializer.data, status=status.HTTP_200_OK)

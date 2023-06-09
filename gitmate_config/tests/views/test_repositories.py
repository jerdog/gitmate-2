import os

from IGitt.Interfaces.Repository import Repository as IGittRepository
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.reverse import reverse
from social_django.models import UserSocialAuth

from gitmate_config.enums import Providers
from gitmate_config.models import Repository
from gitmate_config.tests.test_base import GitmateTestCase
from gitmate_config.views import RepositoryViewSet

from gitmate_config.utils import GitMateUser
from unittest.mock import MagicMock


class TestRepositories(GitmateTestCase):

    def setUp(self):
        super().setUp()

        self.repo_list = RepositoryViewSet.as_view(actions={'get': 'list'})
        self.repo_list_url = reverse('api:repository-list')

        self.repo_detail = RepositoryViewSet.as_view(
            actions={'patch': 'partial_update', 'put': 'update'},
        )

    def test_get_repos(self):
        # Clearing a previously created entry from db
        self.repo.delete()
        self.gl_repo.delete()

        cached_get_repos_request = self.factory.get(self.repo_list_url,
                                                    {'cached': '1'})
        uncached_get_repos_request = self.factory.get(self.repo_list_url,
                                                      {'cached': '0'})
        response = self.repo_list(cached_get_repos_request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        cached_get_repos_request.user = self.user

        response = self.repo_list(cached_get_repos_request)
        # contains github installation repository only
        self.assertEqual(len(response.data), 1)

        uncached_get_repos_request.user = self.user
        response = self.repo_list(uncached_get_repos_request)
        self.assertIn(os.environ['GITHUB_TEST_REPO'],
                      [elem['full_name'] for elem in response.data])
        self.assertIn(os.environ['GITLAB_TEST_REPO'],
                      [elem['full_name'] for elem in response.data])
        self.assertIn('plugins', response.data[0])

        cached_response = self.repo_list(cached_get_repos_request)
        self.assertEqual(cached_response.data, response.data)

    def test_repo_written_in_org(self):
        self.assertEqual(self.repo.org, None)

        uncached_get_repos_request = self.factory.get(self.repo_list_url,
                                                      {'cached': '0'})
        uncached_get_repos_request.user = self.user

        self.repo_list(uncached_get_repos_request)
        self.repo.refresh_from_db()

        self.assertNotEqual(self.repo.org, None)

    def test_activate_repo_with_installation(self):
        url = reverse('api:repository-detail', args=(self.gh_app_repo.pk,))
        activate_repo_request = self.factory.patch(url, {'active': True})
        activate_repo_request.user = self.user
        response = self.repo_detail(
            activate_repo_request, pk=self.gh_app_repo.pk)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        inst_url = 'https://github.com/settings/installations/1'
        self.assertEqual(
            response.data['msg'],
            f'Please visit {inst_url} to configure your installation.')

    def test_repo_renaming(self):
        # Clearing a previously created entry from db
        self.repo.delete()
        self.gl_repo.delete()

        uncached_get_repos_request = self.factory.get(self.repo_list_url,
                                                      {'cached': '0'})
        uncached_get_repos_request.user = self.user

        unmocked_result = GitMateUser(self.user).master_repos(Providers.GITHUB)
        GitMateUser.master_repos = MagicMock(return_value=unmocked_result)
        response = self.repo_list(uncached_get_repos_request)
        self.assertIn(os.environ['GITHUB_TEST_REPO'],
                      [elem['full_name'] for elem in response.data])

        mocked_result = unmocked_result
        list(mocked_result)[0]._repository = \
            'gitmate-test-user/test-mocked-renaming'
        GitMateUser.master_repos = MagicMock(return_value=mocked_result)
        response = self.repo_list(uncached_get_repos_request)
        self.assertIn('gitmate-test-user/test-mocked-renaming',
                      [elem['full_name'] for elem in response.data])

    def test_activate_repo(self):
        url = reverse('api:repository-detail', args=(self.repo.pk,))
        activate_repo_request = self.factory.patch(url, {'active': True})
        activate_repo_request.user = self.user
        response = self.repo_detail(activate_repo_request, pk=self.repo.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('https://localhost:8000/webhooks/github',
                      self.repo.igitt_repo.hooks)

        # Although repo is active, no error :)
        activate_repo_request = self.factory.patch(url, {'active': True})
        activate_repo_request.user = self.user
        response = self.repo_detail(activate_repo_request, pk=self.repo.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        deactivate_repo_request = self.factory.patch(
            url,
            {'active': False},
        )
        deactivate_repo_request.user = self.user
        response = self.repo_detail(deactivate_repo_request, pk=self.repo.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('https://localhost:8000/webhooks/github',
                         self.repo.igitt_repo.hooks)

    def test_set_user(self):
        url = reverse('api:repository-detail', args=(self.repo.pk,))

        # Add an admin user
        admin_user = User.objects.create_user(
            username='max',
            email='max.mustermann@example.com',
            first_name='Max',
            last_name='Mustermann'
        )
        admin_auth = UserSocialAuth(
            user=admin_user, provider=Providers.GITHUB.value, uid=2)
        admin_auth.set_extra_data({
            'access_token': os.environ['GITHUB_TEST_TOKEN']
        })
        admin_auth.save()
        self.repo.admins.add(admin_user)
        self.repo.save()

        request = self.factory.patch(url, {'user': 'max'})
        request.user = self.user
        response = self.repo_detail(request, pk=self.repo.pk)
        self.assertEqual(response.data['user'], 'max')

    def test_igitt_repo_creation(self):
        igitt_repo = self.repo.igitt_repo
        igitt_repo_gl = self.gl_repo.igitt_repo
        self.assertIsInstance(igitt_repo, IGittRepository)
        self.assertIsInstance(igitt_repo_gl, IGittRepository)

    def test_not_implemented_igitt_repo_creation(self):
        self.auth = UserSocialAuth(
            user=self.user, provider='unknownprovider')
        self.auth.set_extra_data({
            'access_token': 'stupidshit'
        })
        self.auth.save()

        with self.assertRaises(NotImplementedError):
            repo = Repository(
                user=self.user,
                provider='unknownprovider',
                full_name='some_repo',
                active=False
            ).igitt_repo

    def test_accessless_repo_deletion(self):
        uncached_get_repos_request = self.factory.get(self.repo_list_url,
                                                      {'cached': '0'})
        uncached_get_repos_request.user = self.user
        response = self.repo_list(uncached_get_repos_request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('gitmate-test-user/delete-test',
                      [elem['full_name'] for elem in response.data])
        no_of_repos_old = len(response.data)

        # Repository `gitmate-test-user/delete-test` deleted via the UI, as
        # the oauth token doesn't have administrator access and it is not
        # advisable creating and sharing a token that does have admin access.

        response = self.repo_list(uncached_get_repos_request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('gitmate-test-user/delete-test',
                         [elem['full_name'] for elem in response.data])

        # ensuring only one repository was deleted from the database
        self.assertEqual(len(response.data), no_of_repos_old - 1)

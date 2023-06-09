"""
This file contains a sample test case for rebaser to be used as
a reference for writing further tests.
"""
from collections import namedtuple
from os import environ
from unittest.mock import patch
from unittest.mock import PropertyMock
import subprocess

from rest_framework import status
from IGitt.GitHub.GitHubComment import GitHubComment
from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest
from IGitt.GitHub.GitHubRepository import GitHubRepository
from IGitt.GitHub.GitHubUser import GitHubUser
from IGitt.GitHub.GitHubCommit import GitHubCommit
from IGitt.GitLab.GitLabComment import GitLabComment
from IGitt.GitLab.GitLabMergeRequest import GitLabMergeRequest
from IGitt.GitLab.GitLabRepository import GitLabRepository
from IGitt.GitLab.GitLabUser import GitLabUser
from IGitt.GitLab.GitLabCommit import GitLabCommit
from IGitt.Interfaces import AccessLevel
from IGitt.Interfaces.Comment import CommentType

from gitmate_config.tests.test_base import GitmateTestCase
from gitmate_config.tests.test_base import StreamMock
from plugins.gitmate_rebaser.responders import verify_command_access


PopenResult = namedtuple('ret', 'stdout wait')


def fake_popen_success(cmd, **kwargs):
    if 'run.py' in cmd:
        return PopenResult(StreamMock('{"status": "success"}'),
                           lambda *args, **kwargs: None)


def fake_popen_failure(cmd, **kwargs):
    if 'run.py' in cmd:
        return PopenResult(
            StreamMock(
                '{"status": "error", "error": "Command \'[\'git\', \'rebase\''
                ', \'master\']\' returned non-zero exit status 128."}'),
            lambda *args, **kwargs: None)


class TestGitmateRebaser(GitmateTestCase):
    def setUp(self):
        super().setUpWithPlugin('rebaser')
        self.repo.settings = [{
            'name': 'rebaser',
            'settings': {
                'enable_rebase': True,
                'fastforward_admin_only': True,
                'enable_squash': True,
                'squash_admin_only': True,
            }
        }]
        self.gl_repo.settings = [{
            'name': 'rebaser',
            'settings': {
                'enable_rebase': True
            }
        }]
        self.github_data = {
            'repository': {'full_name': environ['GITHUB_TEST_REPO'],
                           'id': 49558751},
            'issue': {
                'number': 108,
                'pull_request': {},
            },
            'comment': {'id': 322317220},
            'action': 'created'
        }
        self.github_data_2 = {
            'repository': {'full_name': environ['GITHUB_TEST_REPO'],
                           'id': 49558751},
            'issue': {
                'number': 7,
                'pull_request': {},
            },
            'comment': {'id': 331729393},
            'action': 'created'
        }
        self.gitlab_data = {
            'project': {
                'path_with_namespace': environ['GITLAB_TEST_REPO'],
            },
            'object_attributes': {
                'id': 37544128,
                'noteable_type': 'MergeRequest'
            },
            'merge_request': {'iid': 20}
        }
        self.gh_commit = GitHubCommit(
            self.repo.token, self.repo.full_name,
            'f6d2b7c66372236a090a2a74df2e47f42a54456b')
        self.gl_commit = GitLabCommit(
            self.gl_repo.token, self.gl_repo.full_name,
            'f6d2b7c66372236a090a2a74df2e47f42a54456b')
        self.old_popen = subprocess.Popen

    def tearDown(self):
        subprocess.Popen = self.old_popen

    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'add_comment')
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubRepository, 'get_permission_level')
    def test_github_failed_rebase(
            self, m_get_perm, m_author, m_comment, m_body
    ):
        m_body.return_value = '@{} rebase'.format(
            self.repo.user.username.upper())
        m_author.return_value = GitHubUser(
            self.repo.token, self.repo.user.username)
        m_get_perm.return_value = AccessLevel.CAN_READ
        subprocess.Popen = fake_popen_failure
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.github_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with('Automated rebase failed! Please rebase '
                                     'your pull request manually via the '
                                     'command line.\n\nReason:\n'
                                     '```\nCommand \'[\'git\', \'rebase\', '
                                     '\'master\']\' returned non-zero exit '
                                     'status 128.\n```')

    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'add_comment')
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabRepository, 'get_permission_level')
    def test_gitlab_failed_rebase(
            self, m_get_perm, m_author, m_comment, m_body
    ):
        m_body.return_value = '@{} rebase'.format(self.repo.user.username)
        m_author.return_value = GitLabUser(self.repo.token, 0)
        m_get_perm.return_value = AccessLevel.CAN_READ
        subprocess.Popen = fake_popen_failure
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gitlab_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with('Automated rebase failed! Please rebase '
                                     'your pull request manually via the '
                                     'command line.\n\nReason:\n'
                                     '```\nCommand \'[\'git\', \'rebase\', '
                                     '\'master\']\' returned non-zero exit '
                                     'status 128.\n```')

    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'add_comment')
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubRepository, 'get_permission_level')
    def test_github_successful_rebase(
            self, m_get_perm, m_author, m_comment, m_body
    ):
        m_body.return_value = f'@{self.repo.user.username} rebase'
        m_author.return_value = GitHubUser(
            self.repo.token, self.repo.user.username)
        m_get_perm.return_value = AccessLevel.CAN_READ
        subprocess.Popen = fake_popen_success
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.github_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(
            'Automated rebase with [GitMate.io](https://gitmate.io) was '
            'successful! :tada:')

    @patch.object(GitHubMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'add_comment')
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubRepository, 'get_permission_level')
    def test_github_successful_squash(
            self, m_get_perm, m_author, m_comment, m_body, m_commits
    ):
        m_body.return_value = f'@{self.repo.user.username} squash line1\nline2'
        m_author.return_value = GitHubUser(
            self.repo.token, self.repo.user.username)
        m_get_perm.return_value = AccessLevel.ADMIN
        m_commits.return_value = tuple([self.gh_commit])
        subprocess.Popen = fake_popen_success
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.github_data_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(
            'Automated squash with [GitMate.io](https://gitmate.io) was '
            'successful! :tada:')

    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'add_comment')
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabRepository, 'get_permission_level')
    def test_gitlab_successful_rebase(
            self, m_get_perm, m_author, m_comment, m_body
    ):
        m_body.return_value = '@{} rebase'.format(self.repo.user.username)
        m_author.return_value = GitLabUser(self.repo.token, 0)
        m_get_perm.return_value = AccessLevel.CAN_READ
        subprocess.Popen = fake_popen_success
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gitlab_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(
            'Automated rebase with [GitMate.io](https://gitmate.io) was '
            'successful! :tada:')

    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'add_comment')
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubRepository, 'get_permission_level')
    def test_github_unauthorized(
            self, m_get_perm, m_author, m_comment, m_body
    ):
        m_body.return_value = f'@{self.repo.user.username} rebase'
        m_author.return_value = GitHubUser(
            self.repo.token, self.repo.user.username)
        m_get_perm.return_value = AccessLevel.NONE
        subprocess.Popen = fake_popen_success
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.github_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(
            f'Hey @{self.repo.user.username}, you do not have the access to '
            'perform the rebase action with [GitMate.io](https://gitmate.io). '
            'Please ask a maintainer to give you access. :warning:')

    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'add_comment')
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    def test_irrelevant_comment(self, m_author, m_comment, m_body):
        m_body.return_value = f'Life is full of 0s and 1s'
        m_author.return_value = GitHubUser(
            self.repo.token, self.repo.user.username)
        subprocess.Popen = fake_popen_success
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.github_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_not_called()

    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'repository', new_callable=PropertyMock)
    @patch.object(GitHubRepository, 'get_permission_level')
    def test_verify_command_access(self, m_get_perm, m_repo, m_author):
        merge_admin_only = self.plugin_config.get_settings(
            self.repo)['merge_admin_only']
        fastforward_admin_only = self.plugin_config.get_settings(
            self.repo)['fastforward_admin_only']
        squash_admin_only = self.plugin_config.get_settings(
            self.repo)['squash_admin_only']

        m_repo.return_value = self.repo.igitt_repo
        m_author.return_value = GitHubUser(
            self.repo.token, self.repo.user.username)

        m_comment = GitHubComment(self.repo.token,
                                  self.repo.igitt_repo,
                                  CommentType.ISSUE,
                                  123)

        m_get_perm.return_value = AccessLevel.CAN_WRITE
        self.assertTrue(verify_command_access(m_comment, merge_admin_only,
                                              fastforward_admin_only,
                                              squash_admin_only, 'merge'))

        m_get_perm.return_value = AccessLevel.CAN_WRITE
        self.assertFalse(verify_command_access(m_comment, merge_admin_only,
                                               fastforward_admin_only,
                                               squash_admin_only,
                                               'fastforward'))

        m_get_perm.return_value = AccessLevel.ADMIN
        self.assertTrue(verify_command_access(m_comment, merge_admin_only,
                                              fastforward_admin_only,
                                              squash_admin_only,
                                              'fastforward'))

        m_get_perm.return_value = AccessLevel.CAN_WRITE
        self.assertFalse(verify_command_access(m_comment, merge_admin_only,
                                               fastforward_admin_only,
                                               squash_admin_only, 'squash'))

"""
This file contains a sample test case for weighing_machine to be used as
a reference for writing further tests.
"""
from os import environ
from unittest.mock import patch
from unittest.mock import PropertyMock

from rest_framework import status

from gitmate_config.tests.test_base import GitmateTestCase
from IGitt.GitHub.GitHubCommit import GitHubCommit
from IGitt.GitHub.GitHubIssue import GitHubIssue
from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest
from IGitt.GitLab.GitLabCommit import GitLabCommit
from IGitt.GitLab.GitLabIssue import GitLabIssue
from IGitt.GitLab.GitLabMergeRequest import GitLabMergeRequest


class TestGitmateWeighingMachine(GitmateTestCase):
    def setUp(self):
        super().setUpWithPlugin('weighing_machine')
        self.gh_commit = GitHubCommit(
            self.repo.token, self.repo.full_name,
            'f6d2b7c66372236a090a2a74df2e47f42a54456b')
        self.gl_commit = GitLabCommit(
            self.gl_repo.token, self.gl_repo.full_name,
            'f6d2b7c66372236a090a2a74df2e47f42a54456b')
        self.repo.settings = [{
            'name': 'weighing_machine',
            'settings': {'check_issue_weight_presence': True}
        }]
        self.gl_repo.settings = [{
            'name': 'weighing_machine',
            'settings': {'check_issue_weight_presence': True}
        }]

    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    def test_issue_overweight_presence_github(self, mocked_labels):
        # GitHub API doesn't have issue weight support yet
        data = {
            'repository': {'full_name': environ['GITHUB_TEST_REPO'],
                           'id': 49558751},
            'issue': {'number': 104},
            'action': 'opened'
        }
        response = self.simulate_github_webhook_call('issues', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_labels.assert_not_called()

    @patch.object(GitLabIssue,
                  'weight',
                  new_callable=PropertyMock,
                  return_value=None)
    @patch.object(GitLabIssue,
                  'labels',
                  new_callable=PropertyMock,
                  return_value={'happy-bot'})
    def test_issue_weight_presence_gitlab(self, mocked_labels, _):
        data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'open',
                'iid': 21
            }
        }
        response = self.simulate_gitlab_webhook_call('Issue Hook', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_labels.assert_called_with({'happy-bot', 'weight/missing'})

    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    def test_issue_overweight_github(self, mocked_labels):
        # GitHub API doesn't have issue weight support yet
        data = {
            'repository': {'full_name': environ['GITHUB_TEST_REPO'],
                           'id': 49558751},
            'issue': {'number': 104},
            'action': 'opened'
        }
        response = self.simulate_github_webhook_call('issues', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_labels.assert_not_called()

    @patch.object(GitLabIssue,
                  'weight',
                  new_callable=PropertyMock,
                  return_value=10)
    @patch.object(GitLabIssue,
                  'labels',
                  new_callable=PropertyMock,
                  return_value={'happy-bot'})
    def test_issue_overweight_gitlab(self, mocked_labels, _):
        data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'update',
                'iid': 21
            },
            'changes': {
                'weight': {
                    'previous': None,
                    'current': 8
                }
            }
        }
        response = self.simulate_gitlab_webhook_call('Issue Hook', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_labels.assert_called_with({'happy-bot', 'weight/overweight'})

from os import environ
from unittest.mock import patch

from rest_framework import status

from gitmate_config.tests.test_base import GitmateTestCase
from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest
from IGitt.GitLab.GitLabMergeRequest import GitLabMergeRequest


class TestWelcomeCommenter(GitmateTestCase):

    def setUp(self):
        super().setUpWithPlugin('welcome_commenter')

    @patch.object(GitHubMergeRequest, 'add_comment')
    def test_github(self, mock_add_comment):
        data = {
            'repository': {'full_name': environ['GITHUB_TEST_REPO']},
            'pull_request': {'number': 7},
            'action': 'opened'
        }
        response = self.simulate_github_webhook_call('pull_request', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_add_comment.assert_called_once_with('')

    @patch.object(GitLabMergeRequest, 'add_comment')
    def test_gitlab(self, mock_add_comment):
        data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'open',
                'iid': 2
            }
        }
        response = self.simulate_gitlab_webhook_call(
            'Merge Request Hook', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_add_comment.assert_called_once_with('')
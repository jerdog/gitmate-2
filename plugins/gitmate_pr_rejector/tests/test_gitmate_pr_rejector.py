from os import environ
from unittest.mock import patch
from unittest.mock import PropertyMock

from rest_framework import status

from gitmate_config.tests.test_base import GitmateTestCase
from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest
from IGitt.GitLab.GitLabMergeRequest import GitLabMergeRequest
from IGitt.Interfaces import MergeRequestStates


class TestGitmatePrRejector(GitmateTestCase):
    def setUp(self):
        super().setUpWithPlugin('pr_rejector')

    @patch.object(GitHubMergeRequest, 'head_branch_name',
                  new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'state', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'close')
    @patch.object(GitHubMergeRequest, 'add_comment')
    def test_github(self, m_add_comment, m_close, m_state, m_head_branch_name):
        data = {
            'repository': {'full_name': environ['GITHUB_TEST_REPO'],
                           'id': 49558751},
            'pull_request': {'number': 2},
            'action': 'opened'
        }
        m_head_branch_name.return_value = 'master'
        m_state.return_value = MergeRequestStates.OPEN
        response = self.simulate_github_webhook_call('pull_request', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_add_comment.assert_called_with('Open PR on a different source branch'
                                         ' other than master.')
        m_close.assert_called_once()

    @patch.object(GitHubMergeRequest, 'head_branch_name',
                  new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'state', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'close')
    @patch.object(GitHubMergeRequest, 'add_comment')
    def test_github_with_regex(self, m_add_comment, m_close, m_state,
                               m_head_branch_name):
        data = {
            'repository': {'full_name': environ['GITHUB_TEST_REPO'],
                           'id': 49558751},
            'pull_request': {'number': 2},
            'action': 'opened'
        }
        self.repo.settings = [{
            'name': 'pr_rejector',
            'settings': {
                'branch_names': [r'release\/.*'],
                'message': 'Open PR on a different source branch that '
                           'does not start with `release/`'
            }
        }]
        m_head_branch_name.return_value = 'release/1.0'
        m_state.return_value = MergeRequestStates.OPEN
        response = self.simulate_github_webhook_call('pull_request', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_add_comment.assert_called_with('Open PR on a different source branch'
                                         ' that does not start with `release/`'
                                         )
        m_close.assert_called_once()

    @patch.object(GitLabMergeRequest, 'head_branch_name',
                  new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'state', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'close')
    @patch.object(GitLabMergeRequest, 'add_comment')
    def test_gitlab(self, m_add_comment, m_close, m_state, m_head_branch_name):
        data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'open',
                'iid': 25
            }
        }
        m_head_branch_name.return_value = 'master'
        m_state.return_value = MergeRequestStates.OPEN
        response = self.simulate_gitlab_webhook_call(
            'Merge Request Hook', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_add_comment.assert_called_with('Open PR on a different source branch'
                                         ' other than master.')
        m_close.assert_called_once()

    @patch.object(GitLabMergeRequest, 'head_branch_name',
                  new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'state', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'close')
    @patch.object(GitLabMergeRequest, 'add_comment')
    def test_gitlab_with_regex(self, m_add_comment, m_close, m_state,
                               m_head_branch_name):
        data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'open',
                'iid': 25
            }
        }
        self.gl_repo.settings = [{
            'name': 'pr_rejector',
            'settings': {
                'branch_names': [r'release\/.*'],
                'message': 'Open PR on a different source branch that '
                           'does not start with `release/`'
            }
        }]
        m_head_branch_name.return_value = 'release/1.0'
        m_state.return_value = MergeRequestStates.OPEN
        response = self.simulate_gitlab_webhook_call(
            'Merge Request Hook', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_add_comment.assert_called_with('Open PR on a different source branch'
                                         ' that does not start with `release/`'
                                         )
        m_close.assert_called_once()

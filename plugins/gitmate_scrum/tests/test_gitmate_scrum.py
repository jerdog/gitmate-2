"""
This file contains unit tests for scrum plugin.
"""
from os import environ
from unittest.mock import patch
from unittest.mock import PropertyMock

from IGitt.GitHub.GitHubCommit import GitHubCommit
from IGitt.GitHub.GitHubIssue import GitHubIssue
from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest
from IGitt.GitLab.GitLabCommit import GitLabCommit
from IGitt.GitLab.GitLabIssue import GitLabIssue
from IGitt.GitLab.GitLabMergeRequest import GitLabMergeRequest
from IGitt.Interfaces import MergeRequestStates
from rest_framework import status

from gitmate_config.tests.test_base import GitmateTestCase


class TestGitmateScrum(GitmateTestCase):
    def setUp(self):
        super().setUpWithPlugin('scrum')
        self.gh_commit = GitHubCommit(
            self.repo.token, self.repo.full_name,
            'f6d2b7c66372236a090a2a74df2e47f42a54456b')
        self.gl_commit = GitLabCommit(
            self.gl_repo.token, self.gl_repo.full_name,
            'f6d2b7c66372236a090a2a74df2e47f42a54456b')

    @patch.object(GitHubIssue,
                  'labels',
                  new_callable=PropertyMock,
                  return_value={'dev/blocked'})
    def test_mark_ongoing_github(self, mocked_labels):
        data = {
            'repository': {
                'id': 49558751,
                'full_name': environ['GITHUB_TEST_REPO']
            },
            'assignees': [{'login': 'bb8'}, {'login': 'death-star'}],
            'issue': {'number': 110},
            'action': 'assigned'
        }

        response = self.simulate_github_webhook_call('issues', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_labels.assert_called()
        mocked_labels.assert_called_with({'dev/ongoing'})

    @patch.object(GitLabIssue,
                  'labels',
                  new_callable=PropertyMock,
                  return_value={'dev/blocked'})
    def test_mark_ongoing_gitlab(self, mocked_labels):
        data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'updated',
                'iid': 25
            },
            'changes': {'assignees': {'current': [{'username': 'bb8'}]}}
        }

        response = self.simulate_gitlab_webhook_call('Issue Hook', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_labels.assert_called()
        mocked_labels.assert_called_with({'dev/ongoing'})

    @patch.object(GitHubCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'state', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'labels', new_callable=PropertyMock)
    def test_mark_code_review_github(
            self, m_labels, m_state, m_commits, m_msg
    ):
        m_labels.return_value = {'dev/ongoing'}
        m_commits.return_value = {self.gh_commit}
        m_state.return_value = MergeRequestStates.OPEN
        m_msg.return_value = 'Yippity yappety ya ya\n\nQA: #125'
        data = {
            'repository': {'full_name': self.repo.full_name, 'id': 49558751},
            'pull_request': {'number': 0},
            'action': 'opened'
        }
        response = self.simulate_github_webhook_call('pull_request', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_msg.assert_called()
        m_commits.assert_called()
        m_labels.assert_called()
        m_labels.assert_called_with({'dev/code-review'})

    @patch.object(GitLabCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'state', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'labels', new_callable=PropertyMock)
    def test_mark_code_review_gitlab(
            self, m_labels, m_state, m_commits, m_msg
    ):
        m_labels.return_value = {'dev/ongoing'}
        m_commits.return_value = {self.gl_commit}
        m_state.return_value = MergeRequestStates.OPEN
        m_msg.return_value = 'Yippity yappety ya ya\n\nQA: #125'
        data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'open',
                'oldrev': 'gitmatesavestheday',
                'iid': 2
            }
        }
        response = self.simulate_gitlab_webhook_call(
            'Merge Request Hook', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_msg.assert_called()
        m_commits.assert_called()
        m_labels.assert_called()
        m_labels.assert_called_with({'dev/code-review'})

    @patch.object(GitHubCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'state', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'labels', new_callable=PropertyMock)
    def test_mark_acceptance_github(
            self, m_labels, m_state, m_commits, m_msg
    ):
        m_labels.return_value = {'dev/ongoing'}
        m_commits.return_value = {self.gh_commit}
        m_state.return_value = MergeRequestStates.MERGED
        m_msg.return_value = 'Yippity yappety ya ya\n\nQA: #125'
        data = {
            'repository': {'full_name': self.repo.full_name, 'id': 49558751},
            'pull_request': {'number': 0},
            'action': 'synchronize'
        }
        response = self.simulate_github_webhook_call('pull_request', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_msg.assert_called()
        m_commits.assert_called()
        m_labels.assert_called()
        m_labels.assert_called_with({'dev/acceptance-QA'})

    @patch.object(GitLabCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'state', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'labels', new_callable=PropertyMock)
    def test_mark_acceptance_gitlab(
            self, m_labels, m_state, m_commits, m_msg
    ):
        m_labels.return_value = {'dev/ongoing'}
        m_commits.return_value = {self.gl_commit}
        m_state.return_value = MergeRequestStates.MERGED
        m_msg.return_value = 'Yippity yappety ya ya\n\nQA: #125'
        data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'synchronize',
                'oldrev': 'gitmatesavestheday',
                'iid': 2
            }
        }
        response = self.simulate_gitlab_webhook_call(
            'Merge Request Hook', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_msg.assert_called()
        m_commits.assert_called()
        m_labels.assert_called()
        m_labels.assert_called_with({'dev/acceptance-QA'})

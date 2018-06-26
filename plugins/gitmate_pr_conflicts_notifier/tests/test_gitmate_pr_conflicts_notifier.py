from os import environ
from unittest.mock import patch
from unittest.mock import PropertyMock

from rest_framework import status

from gitmate_config.tests.test_base import GitmateTestCase
from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest
from IGitt.GitLab.GitLabMergeRequest import GitLabMergeRequest


class TestGitmatePrConflictsNotifier(GitmateTestCase):
    def setUp(self):
        super().setUpWithPlugin('pr_conflicts_notifier')
        self.github_data = {
            'repository': {'full_name': environ['GITHUB_TEST_REPO'],
                           'id': 49558751},
            'pull_request': {'number': 7},
            'action': 'synchronize'
        }
        self.gitlab_data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'open',
                'iid': 2
            }
        }

    @patch.object(GitHubMergeRequest, 'add_comment')
    @patch.object(GitHubMergeRequest, 'mergeable', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'labels', new_callable=PropertyMock)
    def test_github(self, m_labels, m_mergeable, m_add_comment):
        m_mergeable.return_value = True
        m_labels.return_value = set()
        response = self.simulate_github_webhook_call('pull_request',
                                                     self.github_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(m_labels.return_value, set())
        m_labels.assert_called_with(set())
        m_add_comment.assert_not_called()
        m_labels.return_value = set()
        m_mergeable.return_value = False
        response = self.simulate_github_webhook_call('pull_request',
                                                     self.github_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_labels.assert_called_with({'needs rebase'})
        m_add_comment.assert_called_with('This PR has merge conflicts, please'
                                         ' do a manual rebase and resolve '
                                         'conflicts.')

    @patch.object(GitLabMergeRequest, 'add_comment')
    @patch.object(GitLabMergeRequest, 'mergeable', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'labels', new_callable=PropertyMock)
    def test_gitlab(self, m_labels, m_mergeable, m_add_comment):
        m_mergeable.return_value = True
        m_labels.return_value = {'needs rebase'}
        response = self.simulate_gitlab_webhook_call('Merge Request Hook',
                                                     self.gitlab_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_labels.assert_called_with(set())
        m_add_comment.assert_not_called()
        m_labels.return_value = set()
        m_mergeable.return_value = False
        response = self.simulate_gitlab_webhook_call('Merge Request Hook',
                                                     self.gitlab_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_labels.assert_called_with({'needs rebase'})
        m_add_comment.assert_called_with('This PR has merge conflicts, please'
                                         ' do a manual rebase and resolve '
                                         'conflicts.')

from os import environ
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import PropertyMock

from rest_framework import status

from gitmate_config.tests.test_base import GitmateTestCase
from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest
from IGitt.GitHub.GitHubIssue import GitHubIssue
from IGitt.GitHub.GitHubCommit import GitHubCommit
from IGitt.GitLab.GitLabMergeRequest import GitLabMergeRequest
from IGitt.GitLab.GitLabIssue import GitLabIssue
from IGitt.GitLab.GitLabCommit import GitLabCommit


class TestAutoLabelPendingOrWip(GitmateTestCase):

    def setUp(self):
        self.setUpWithPlugin('auto_label_pending_or_wip')
        self.settings = [{
            'name': 'auto_label_pending_or_wip',
            'settings': {
                'enable_fixes_vs_closes': True
            }
        }]
        self.repo.settings = self.settings
        self.gl_repo.settings = self.settings
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
        self.gh_commit = GitHubCommit(
            self.repo.token, self.repo.full_name,
            '3f2a3b37a2943299c589004c2a5be132e9440cba')
        self.gl_commit = GitLabCommit(
            self.gl_repo.token, self.gl_repo.full_name,
            'f6d2b7c66372236a090a2a74df2e47f42a54456b')

    @patch.object(GitHubMergeRequest, 'labels', new_callable=PropertyMock)
    def test_github_change_label_to_process_pending(self, mocked_labels):
        mocked_labels.return_value.add = MagicMock()
        response = self.simulate_github_webhook_call(
            'pull_request', self.github_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_labels().add.assert_called_with('process/pending_review')

    @patch.object(GitHubMergeRequest, 'title',
                  new_callable=PropertyMock,
                  return_value='WIP: Fühl mich betrunken')
    @patch.object(GitHubMergeRequest, 'labels', new_callable=PropertyMock)
    def test_github_change_label_to_process_wip(self, mocked_labels, *args):
        mocked_labels.return_value.add = MagicMock()
        response = self.simulate_github_webhook_call(
            'pull_request', self.github_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_labels().add.assert_called_with('process/WIP')

    @patch.object(GitHubMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitHubCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'add_comment')
    @patch.object(GitHubMergeRequest, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'will_fix_issues',
                  new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'will_close_issues',
                  new_callable=PropertyMock)
    def test_github_fixes_without_bug_label(self, m_will_close_issues,
                                            m_will_fix_issues, m_iss_labels,
                                            m_labels, m_add_comment, m_message,
                                            m_commits):
        m_labels.return_value = set()
        m_commits.return_value = tuple([self.gh_commit])
        m_message.return_value = 'Fixes #1'
        m_will_fix_issues.return_value = {
            GitHubIssue(self.repo.token, self.repo.full_name, 1)
        }
        m_will_close_issues.return_value = set()
        m_iss_labels.return_value = {'type/something'}
        response = self.simulate_github_webhook_call('pull_request',
                                                     self.github_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_labels.assert_called_with({'process/WIP'})
        m_add_comment.assert_called_with('`Fixes` is used but referenced issue'
                                         " doesn't have a bug label, if issue "
                                         'is updated to include the bug label '
                                         'then ask a maintainer to add bug '
                                         'label else use `Closes`.')

    @patch.object(GitHubMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitHubCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'add_comment')
    @patch.object(GitHubMergeRequest, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'will_fix_issues',
                  new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'will_close_issues',
                  new_callable=PropertyMock)
    def test_github_disable_checking_keywords(self, m_will_close_issues,
                                              m_will_fix_issues, m_iss_labels,
                                              m_labels, m_add_comment,
                                              m_message, m_commits):
        self.repo.settings = [{
            'name': 'auto_label_pending_or_wip',
            'settings': {
                'enable_fixes_vs_closes': False
            }
        }]

        m_labels.return_value = set()
        m_commits.return_value = tuple([self.gh_commit])
        m_message.return_value = 'Fixes #1'
        m_will_fix_issues.return_value = {
            GitHubIssue(self.repo.token, self.repo.full_name, 1)
        }
        m_will_close_issues.return_value = set()
        m_iss_labels.return_value = {'type/something'}
        response = self.simulate_github_webhook_call('pull_request',
                                                     self.github_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_add_comment.assert_not_called()

    @patch.object(GitHubMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitHubCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'add_comment')
    @patch.object(GitHubMergeRequest, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'will_fix_issues',
                  new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'will_close_issues',
                  new_callable=PropertyMock)
    def test_github_closes_with_bug_label(self, m_will_close_issues,
                                          m_will_fix_issues, m_iss_labels,
                                          m_labels, m_add_comment, m_message,
                                          m_commits):
        m_labels.return_value = set()
        m_commits.return_value = tuple([self.gh_commit])
        m_message.return_value = 'Closes #1'
        m_will_close_issues.return_value = {
            GitHubIssue(self.repo.token, self.repo.full_name, 1)
        }
        m_will_fix_issues.return_value = set()
        m_iss_labels.return_value = {'type/bug'}
        response = self.simulate_github_webhook_call('pull_request',
                                                     self.github_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_add_comment.assert_called_with('`Closes` is used but issue has a bug'
                                         ' label, if issue is updated to '
                                         'remove the bug label then ask a '
                                         'maintainer to remove bug label else '
                                         'use `Fixes`.')
        m_labels.assert_called_with({'process/WIP'})

    @patch.object(GitLabMergeRequest, 'labels', new_callable=PropertyMock)
    def test_gitlab_change_label_to_process_pending(self, mocked_labels):
        mocked_labels.return_value.add = MagicMock()
        response = self.simulate_gitlab_webhook_call(
            'Merge Request Hook', self.gitlab_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_labels().add.assert_called_with('process/pending_review')

    @patch.object(GitLabMergeRequest, 'title',
                  new_callable=PropertyMock,
                  return_value='WIP: Fühl mich betrunken')
    @patch.object(GitLabMergeRequest, 'labels', new_callable=PropertyMock)
    def test_gitlab_change_label_to_process_wip(self, mocked_labels, *args):
        mocked_labels.return_value.add = MagicMock()
        response = self.simulate_gitlab_webhook_call(
            'Merge Request Hook', self.gitlab_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_labels().add.assert_called_with('process/WIP')

    @patch.object(GitLabMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitLabCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'add_comment')
    @patch.object(GitLabMergeRequest, 'labels', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'will_fix_issues',
                  new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'will_close_issues',
                  new_callable=PropertyMock)
    def test_gitlab_fixes_without_bug_label(self, m_will_close_issues,
                                            m_will_fix_issues, m_iss_labels,
                                            m_labels, m_add_comment, m_message,
                                            m_commits):
        m_labels.return_value = set()
        m_commits.return_value = tuple([self.gl_commit])
        m_message.return_value = 'Fixes #1'
        m_will_fix_issues.return_value = {
            GitLabIssue(self.gl_repo.token, self.gl_repo.full_name, 1)
        }
        m_will_close_issues.return_value = set()
        m_iss_labels.return_value = {'type/something'}
        response = self.simulate_gitlab_webhook_call('Merge Request Hook',
                                                     self.gitlab_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_add_comment.assert_called_with('`Fixes` is used but referenced issue'
                                         " doesn't have a bug label, if issue "
                                         'is updated to include the bug label '
                                         'then ask a maintainer to add bug '
                                         'label else use `Closes`.')
        m_labels.assert_called_with({'process/WIP'})

    @patch.object(GitLabMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitLabCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'add_comment')
    @patch.object(GitLabMergeRequest, 'labels', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'will_fix_issues',
                  new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'will_close_issues',
                  new_callable=PropertyMock)
    def test_gitlab_closes_with_bug_label(self, m_will_close_issues,
                                          m_will_fix_issues, m_iss_labels,
                                          m_labels, m_add_comment, m_message,
                                          m_commits):
        m_labels.return_value = set()
        m_commits.return_value = tuple([self.gl_commit])
        m_message.return_value = 'Closes #1'
        m_will_close_issues.return_value = {
            GitLabIssue(self.gl_repo.token, self.gl_repo.full_name, 1)
        }
        m_will_fix_issues.return_value = set()
        m_iss_labels.return_value = {'type/bug'}
        response = self.simulate_gitlab_webhook_call('Merge Request Hook',
                                                     self.gitlab_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_add_comment.assert_called_with('`Closes` is used but issue has a bug'
                                         ' label, if issue is updated to '
                                         'remove the bug label then ask a '
                                         'maintainer to remove bug label else '
                                         'use `Fixes`.')
        m_labels.assert_called_with({'process/WIP'})

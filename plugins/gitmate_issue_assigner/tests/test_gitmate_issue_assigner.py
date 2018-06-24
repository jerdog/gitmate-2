from os import environ
from unittest.mock import patch
from unittest.mock import PropertyMock

from rest_framework import status

from gitmate_config.tests.test_base import GitmateTestCase
from IGitt.GitHub.GitHubIssue import GitHubIssue
from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest
from IGitt.GitHub.GitHubCommit import GitHubCommit
from IGitt.GitHub.GitHubUser import GitHubUser
from IGitt.GitLab.GitLabIssue import GitLabIssue
from IGitt.GitLab.GitLabMergeRequest import GitLabMergeRequest
from IGitt.GitLab.GitLabCommit import GitLabCommit
from IGitt.GitLab.GitLabUser import GitLabUser
from IGitt.Interfaces import IssueStates
from IGitt.Interfaces.CommitStatus import Status


class TestIssueAssigner(GitmateTestCase):
    def setUp(self):
        super().setUpWithPlugin('issue_assigner')

        self.settings = [
            {
                'name': 'issue_assigner',
                'settings': {
                    'keywords': {
                        'apples': 'apples',
                        'spaceships': 'spaceships, ',
                        'bears': 'bears',
                        'bear-related': 'bears, stupidshit',
                    },
                    'enable_auto_assign': True,
                }
            }
        ]
        self.repo.settings = self.settings
        self.gl_repo.settings = self.settings
        self.gh_commit = GitHubCommit(
            self.repo.token, self.repo.full_name,
            '3f2a3b37a2943299c589004c2a5be132e9440cba')
        self.gl_commit = GitLabCommit(
            self.gl_repo.token, self.gl_repo.full_name,
            'f6d2b7c66372236a090a2a74df2e47f42a54456b')

    @patch.object(GitHubIssue, 'description', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'title', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github(self, m_assign, m_title, m_desc):
        # set some random summary
        m_title.return_value = 'Shape of you'
        m_desc.return_value = 'Make coala bears sing this song!'

        data = {
            'repository': {'full_name': environ['GITHUB_TEST_REPO'],
                           'id': 49558751},
            'issue': {'number': 104},
            'action': 'opened'
        }

        response = self.simulate_github_webhook_call('issues', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        m_assign.assert_any_call('bear-related')
        m_assign.assert_any_call('bears')

    @patch.object(GitHubMergeRequest, 'add_comment', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'author', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubCommit, 'combined_status', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'state', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitHubCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github_auto_assign(self, m_assign, m_message, m_commits, m_state,
                                m_combined_status, m_assignees, m_author,
                                m_add_comment):
        m_commits.return_value = tuple([self.gh_commit])
        m_message.return_value = 'Closes #1'
        # Issue is closed, so this issue will not be assigned
        m_state.return_value = IssueStates.CLOSED
        m_combined_status.return_value = Status.SUCCESS
        m_assignees.return_value = set()
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        data = {
            'repository': {'full_name': environ['GITHUB_TEST_REPO'],
                           'id': 49558751},
            'pull_request': {'number': 113},
            'action': 'opened'
        }

        response = self.simulate_github_webhook_call('pull_request', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_assign.assert_not_called()
        m_add_comment.assert_not_called()
        # Issue is in open state, so this issue is allowed to be assigned
        m_state.return_value = IssueStates.OPEN
        # Issue is already assigned to author of the pull request
        m_assignees.return_value = {
            GitHubUser(self.repo.token, self.repo.user.username)
        }
        response = self.simulate_github_webhook_call('pull_request', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_assign.assert_not_called()
        m_add_comment.assert_not_called()
        m_assignees.return_value = set()
        response = self.simulate_github_webhook_call('pull_request', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_assign.assert_called_with(self.repo.user.username)
        m_add_comment.assert_not_called()

    @patch.object(GitHubMergeRequest, 'closes_issues',
                  new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'add_comment')
    @patch.object(GitHubMergeRequest, 'author', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubCommit, 'combined_status', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'state', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitHubCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github_falied_auto_assign(self, m_assign, m_message, m_commits,
                                       m_state, m_combined_status, m_assignees,
                                       m_author, m_add_comment,
                                       m_closes_issues):
        m_commits.return_value = tuple([self.gh_commit])
        m_message.return_value = 'Closes #1'
        m_closes_issues.return_value = {
            GitHubIssue(self.repo.token, self.repo.full_name, 1)
        }
        m_state.return_value = IssueStates.OPEN
        m_combined_status.return_value = Status.SUCCESS
        m_assignees.return_value = {
            GitHubUser(self.repo.token, 'Vamshi99')
        }
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        data = {
            'repository': {'full_name': environ['GITHUB_TEST_REPO'],
                           'id': 49558751},
            'pull_request': {'number': 113},
            'action': 'opened'
        }

        response = self.simulate_github_webhook_call('pull_request', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_assign.assert_not_called()
        m_add_comment.assert_called_with(
            'Sorry, but the issues https://github.com/gitmate-test-user/test/'
            'issues/1 are assigned to someone else. Please try working on '
            'some other issues.'),

    @patch.object(GitHubMergeRequest, 'add_comment', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'author', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubCommit, 'combined_status', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'state', new_callable=PropertyMock)
    @patch.object(GitHubMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitHubCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github_disable_auto_assign(self, m_assign, m_message, m_commits,
                                        m_state, m_combined_status,
                                        m_assignees, m_author, m_add_comment):
        self.repo.settings = [
            {
                'name': 'issue_assigner',
                'settings': {
                    'enable_auto_assign': False,
                }
            }
        ]
        m_commits.return_value = tuple([self.gh_commit])
        m_message.return_value = 'Closes #1'
        m_state.return_value = IssueStates.OPEN
        m_combined_status.return_value = Status.SUCCESS
        m_assignees.return_value = set()
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        data = {
            'repository': {'full_name': environ['GITHUB_TEST_REPO'],
                           'id': 49558751},
            'pull_request': {'number': 113},
            'action': 'opened'
        }

        response = self.simulate_github_webhook_call('pull_request', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_assign.assert_not_called()
        m_add_comment.assert_not_called()

    @patch.object(GitLabIssue, 'description', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'title', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assign')
    def test_gitlab(self, m_assign, m_title, m_desc):
        # set some random summary
        m_title.return_value = 'Shape of you'
        m_desc.return_value = 'Make coala bears sing this song!'

        data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'open',
                'iid': 21
            }
        }

        response = self.simulate_gitlab_webhook_call('Issue Hook', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        m_assign.assert_any_call('bear-related')
        m_assign.assert_any_call('bears')

    @patch.object(GitLabUser, 'username', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'closes_issues',
                  new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'add_comment')
    @patch.object(GitLabMergeRequest, 'author', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabCommit, 'combined_status', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'state', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitLabCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assign')
    def test_gitlab_auto_assign(self, m_assign, m_message, m_commits, m_state,
                                m_combined_status, m_assignees, m_author,
                                m_add_comment, m_closes_issues, m_username):
        m_commits.return_value = tuple([self.gl_commit])
        m_message.return_value = 'Closes #1'
        m_closes_issues.return_value = {
            GitLabIssue(self.gl_repo.token, self.gl_repo.full_name, 1)
        }
        m_state.return_value = IssueStates.OPEN
        m_combined_status.return_value = Status.SUCCESS
        m_assignees.return_value = set()
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        m_username.return_value = 'sils'
        data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'open',
                'iid': 25
            }
        }
        response = self.simulate_gitlab_webhook_call('Merge Request Hook',
                                                     data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_assign.assert_called_with('sils')
        m_add_comment.assert_not_called()

    @patch.object(GitLabMergeRequest, 'closes_issues',
                  new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'add_comment')
    @patch.object(GitLabMergeRequest, 'author', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabCommit, 'combined_status', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'state', new_callable=PropertyMock)
    @patch.object(GitLabMergeRequest, 'commits', new_callable=PropertyMock)
    @patch.object(GitLabCommit, 'message', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assign')
    def test_gitlab_failed_auto_assign(self, m_assign, m_message, m_commits,
                                       m_state, m_combined_status, m_assignees,
                                       m_author, m_add_comment,
                                       m_closes_issues):
        m_commits.return_value = tuple([self.gl_commit])
        m_message.return_value = 'Closes #1'
        m_closes_issues.return_value = {
            GitLabIssue(self.gl_repo.token, self.gl_repo.full_name, 1)
        }
        m_state.return_value = IssueStates.OPEN
        m_combined_status.return_value = Status.SUCCESS
        m_assignees.return_value = {GitLabUser(self.gl_repo.token, 2)}
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'open',
                'iid': 25
            }
        }
        response = self.simulate_gitlab_webhook_call('Merge Request Hook',
                                                     data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_assign.assert_not_called()
        m_add_comment.assert_called_with(
            'Sorry, but the issues https://gitlab.com/gitmate-test-user/test/'
            'issues/1 are assigned to someone else. Please try working on '
            'some other issues.'),

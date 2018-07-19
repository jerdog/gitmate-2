from os import environ
from unittest.mock import patch
from unittest.mock import PropertyMock

from rest_framework import status

from gitmate_config.tests.test_base import GitmateTestCase
from IGitt.GitHub.GitHubIssue import GitHubIssue
from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest
from IGitt.GitHub.GitHubCommit import GitHubCommit
from IGitt.GitHub.GitHubComment import GitHubComment
from IGitt.GitHub.GitHubUser import GitHubUser
from IGitt.GitHub.GitHubOrganization import GitHubOrganization
from IGitt.GitHub.GitHubRepository import GitHubRepository
from IGitt.GitLab.GitLabIssue import GitLabIssue
from IGitt.GitLab.GitLabMergeRequest import GitLabMergeRequest
from IGitt.GitLab.GitLabCommit import GitLabCommit
from IGitt.GitLab.GitLabUser import GitLabUser
from IGitt.GitLab.GitLabComment import GitLabComment
from IGitt.GitLab.GitLabOrganization import GitLabOrganization
from IGitt.GitLab.GitLabRepository import GitLabRepository
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
                    'enable_assign_request': True,
                    'blocked_labels': ['status/blocked'],
                    'blocked_assignees': ['gitmate-bot'],
                    'label_numbers': {
                        'difficulty/newcomer': 1
                    },
                    'difficulty_order': ['newcomer', 'low']
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
        self.gh_comment = {
            'repository': {'full_name': self.repo.full_name, 'id': 49558751},
            'issue': {'number': 143},
            'comment': {'id': 0},
            'action': 'created'
        }
        self.gl_comment = {
            'project': {'path_with_namespace': self.gl_repo.full_name},
            'object_attributes': {
                'action': 'open',
                'id': 25,
                'iid': 0,
                'noteable_type': 'Issue'
            },
            'issue': {'iid': 21}
        }

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

    @patch.object(GitHubIssue, 'add_comment')
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github_irrelevant_comment(self, m_assign, m_body, m_author,
                                       m_assignees, m_comment):
        m_body.return_value = '@gitmate-bot hey!'
        m_assignees.return_value = set()
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.gh_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_not_called()
        m_assign.assert_not_called()

    @patch.object(GitHubIssue, 'add_comment')
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'unassign')
    def test_github_unassign_failure(self, m_unassign, m_body, m_author,
                                     m_assignees, m_comment):
        m_body.return_value = '@gitmate-bot unassign'
        m_assignees.return_value = set()
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.gh_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@{self.repo.user.username}, You are '
                                     'not an assignee of this issue.')
        m_unassign.assert_not_called()

    @patch.object(GitHubIssue, 'add_comment')
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'unassign')
    def test_github_unassign_success(self, m_unassign, m_body, m_author,
                                     m_assignees, m_comment):
        m_body.return_value = '@gitmate-bot unassign'
        m_assignees.return_value = {
            GitHubUser(self.repo.token, self.repo.user.username)
        }
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.gh_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_not_called()
        m_unassign.assert_called_once()

    @patch.object(GitHubIssue, 'add_comment')
    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github_assigned(self, m_assign, m_body, m_author, m_assignees,
                             m_labels, m_comment):
        m_body.return_value = '@gitmate-bot assign'
        m_assignees.return_value = {
            GitHubUser(self.repo.token, self.repo.user.username)
        }
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.gh_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@{self.repo.user.username} This issue '
                                     'is already assigned to you.')
        m_assign.assert_not_called()
        m_assignees.return_value = {
            GitHubUser(self.repo.token, 'sils')
        }
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.gh_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@{self.repo.user.username} This issue '
                                     'is assigned to someone else, try to work'
                                     ' on another issue.')
        m_assign.assert_not_called()

    @patch.object(GitHubIssue, 'add_comment')
    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github_blocked_label(self, m_assign, m_body, m_author,
                                  m_assignees, m_labels, m_comment):
        m_body.return_value = '@gitmate-bot assign'
        m_assignees.return_value = set()
        m_labels.return_value = {'status/blocked'}
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.gh_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@{self.repo.user.username} Assignment '
                                     'to this issue is blocked.')
        m_assign.assert_not_called()

    @patch.object(GitHubIssue, 'add_comment')
    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github_blocked_assignee(self, m_assign, m_body, m_author,
                                     m_assignees, m_labels, m_comment):
        m_body.return_value = '@gitmate-bot assign'
        m_assignees.return_value = set()
        m_author.return_value = GitHubUser(self.repo.token, 'gitmate-bot')
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.gh_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@gitmate-bot You aren\'t '
                                     'allowed to get assigned to any issue.')
        m_assign.assert_not_called()

    @patch.object(GitHubIssue, 'add_comment')
    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubRepository, 'filter_issues')
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github_max_labelled_issues(self, m_assign, m_body, m_author,
                                        m_repo_issues, m_assignees,
                                        m_labels, m_comment):
        m_labels.return_value = {'difficulty/newcomer'}
        m_body.return_value = '@gitmate-bot assign'
        m_assignees.return_value = set()
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        m_repo_issues.return_value = {
            GitHubIssue(self.repo.token, self.repo.full_name, 1),
        }
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.gh_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@{self.repo.user.username} You have '
                                     'crossed limit of working on '
                                     '`difficulty/newcomer` labelled issues.')
        m_assign.assert_not_called()

    @patch.object(GitHubIssue, 'add_comment')
    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubOrganization, 'filter_issues')
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github_org_max_labelled_issues(self, m_assign, m_body, m_author,
                                            m_org_issues, m_assignees,
                                            m_labels, m_comment):
        self.repo.settings = [
            {
                'name': 'issue_assigner',
                'settings': {
                    'enable_assign_request': True,
                    'label_numbers': {
                        'difficulty/newcomer': 1
                    },
                    'org_level': True
                }
            }
        ]
        m_labels.return_value = {'difficulty/newcomer'}
        m_body.return_value = '@gitmate-bot assign'
        m_assignees.return_value = set()
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        m_org_issues.return_value = {
            GitHubIssue(self.repo.token, self.repo.full_name, 1),
        }
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.gh_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@{self.repo.user.username} You have '
                                     'crossed limit of working on '
                                     '`difficulty/newcomer` labelled issues.')
        m_assign.assert_not_called()

    @patch.object(GitHubIssue, 'add_comment')
    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubRepository, 'filter_issues')
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github_difficulty_order(self, m_assign, m_body, m_author,
                                     m_repo_issues, m_assignees,
                                     m_labels, m_comment):
        m_labels.return_value = {'low'}
        m_body.return_value = '@gitmate-bot assign'
        m_repo_issues.return_value = set()
        m_assignees.return_value = set()
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.gh_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@{self.repo.user.username} You need to '
                                     'solve `newcomer` labelled issues '
                                     'first.')
        m_assign.assert_not_called()

    @patch.object(GitHubIssue, 'add_comment')
    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubOrganization, 'filter_issues')
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github_org_difficulty_order(self, m_assign, m_body, m_author,
                                         m_org_issues, m_assignees,
                                         m_labels, m_comment):
        self.repo.settings = [
            {
                'name': 'issue_assigner',
                'settings': {
                    'enable_assign_request': True,
                    'difficulty_order': ['newcomer', 'low'],
                    'org_level': True
                }
            }
        ]
        m_labels.return_value = {'low'}
        m_body.return_value = '@gitmate-bot assign'
        m_assignees.return_value = set()
        m_org_issues.return_value = set()
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.gh_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@{self.repo.user.username} You need to '
                                     'solve `newcomer` labelled issues '
                                     'first.')
        m_assign.assert_not_called()

    @patch.object(GitHubIssue, 'add_comment')
    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitHubRepository, 'filter_issues')
    @patch.object(GitHubComment, 'author', new_callable=PropertyMock)
    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    @patch.object(GitHubIssue, 'assign')
    def test_github_correct_difficulty_order(self, m_assign, m_body, m_author,
                                             m_repo_issues, m_assignees,
                                             m_labels, m_comment):
        m_labels.return_value = {'low'}
        m_assignees.return_value = set()
        m_body.return_value = '@gitmate-bot assign'
        m_repo_issues.return_value = {
            GitHubIssue(self.repo.token, self.repo.full_name, 1),
            GitHubIssue(self.repo.token, self.repo.full_name, 2)
        }
        m_author.return_value = GitHubUser(self.repo.token,
                                           self.repo.user.username)
        response = self.simulate_github_webhook_call('issue_comment',
                                                     self.gh_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_assign.assert_called_once()

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

    @patch.object(GitLabUser, 'username', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'add_comment')
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assign')
    def test_gitlab_irrelevant_comment(self, m_assign, m_body, m_author,
                                       m_assignees, m_comment, m_username):
        m_body.return_value = '@gitmate-bot hey!'
        m_assignees.return_value = set()
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        m_username.return_value = 'sils'
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gl_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_not_called()
        m_assign.assert_not_called()

    @patch.object(GitLabUser, 'username', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'add_comment')
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'unassign')
    def test_gitlab_unassign_failure(self, m_unassign, m_body, m_author,
                                     m_assignees, m_comment, m_username):
        m_body.return_value = '@gitmate-bot unassign'
        m_assignees.return_value = set()
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        m_username.return_value = 'sils'
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gl_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@sils, You are not an assignee '
                                     'of this issue.')
        m_unassign.assert_not_called()

    @patch.object(GitLabUser, 'username', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'add_comment')
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'unassign')
    def test_gitlab_unassign_success(self, m_unassign, m_body, m_author,
                                     m_assignees, m_comment, m_username):
        m_body.return_value = '@gitmate-bot unassign'
        m_assignees.return_value = {
            GitLabUser(self.gl_repo.token, 1)
        }
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        m_username.return_value = 'sils'
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gl_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_not_called()
        m_unassign.assert_called()

    @patch.object(GitLabUser, 'username', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'add_comment')
    @patch.object(GitLabIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assign')
    def test_gitlab_assigned(self, m_assign, m_body, m_author, m_assignees,
                             m_labels, m_comment, m_username):
        m_body.return_value = '@gitmate-bot assign'
        m_assignees.return_value = {
            GitLabUser(self.gl_repo.token, 1)
        }
        m_author.return_value = GitLabUser(self.gl_repo.token, 2)
        m_username.return_value = 'sils'
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gl_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@sils This issue is assigned to someone'
                                     ' else, try to work on another issue.')
        m_assign.assert_not_called()
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gl_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@sils This issue is already assigned '
                                     'to you.')
        m_assign.assert_not_called()

    @patch.object(GitLabUser, 'username', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'add_comment')
    @patch.object(GitLabIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assign')
    def test_gitlab_blocked_label(self, m_assign, m_body, m_author,
                                  m_assignees, m_labels, m_comment,
                                  m_username):
        m_body.return_value = '@gitmate-bot assign'
        m_assignees.return_value = set()
        m_labels.return_value = {'status/blocked'}
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        m_username.return_value = 'sils'
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gl_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@sils Assignment to this issue is '
                                     'blocked.')
        m_assign.assert_not_called()

    @patch.object(GitLabUser, 'username', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'add_comment')
    @patch.object(GitLabIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assign')
    def test_gitlab_blocked_assignee(self, m_assign, m_body, m_author,
                                     m_assignees, m_labels, m_comment,
                                     m_username):
        m_body.return_value = '@gitmate-bot assign'
        m_assignees.return_value = set()
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        m_username.return_value = 'gitmate-bot'
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gl_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@gitmate-bot You aren\'t '
                                     'allowed to get assigned to any issue.')
        m_assign.assert_not_called()

    @patch.object(GitLabUser, 'username', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'add_comment')
    @patch.object(GitLabIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabRepository, 'filter_issues')
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assign')
    def test_gitlab_max_labelled_issues(self, m_assign, m_body, m_author,
                                        m_repo_issues, m_assignees,
                                        m_labels, m_comment, m_username):
        m_labels.return_value = {'difficulty/newcomer'}
        m_body.return_value = '@gitmate-bot assign'
        m_assignees.return_value = set()
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        m_username.return_value = 'sils'
        m_repo_issues.return_value = {
            GitLabIssue(self.gl_repo.token, self.gl_repo.full_name, 1),
        }
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gl_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@sils You have crossed limit of working'
                                     ' on `difficulty/newcomer` labelled '
                                     'issues.')
        m_assign.assert_not_called()

    @patch.object(GitLabUser, 'username', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'add_comment')
    @patch.object(GitLabIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabRepository, 'filter_issues')
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assign')
    def test_gitlab_difficulty_order(self, m_assign, m_body, m_author,
                                     m_repo_issues, m_assignees,
                                     m_labels, m_comment, m_username):
        m_labels.return_value = {'low'}
        m_body.return_value = '@gitmate-bot assign'
        m_assignees.return_value = set()
        m_repo_issues.return_value = set()
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        m_username.return_value = 'sils'
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gl_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@sils You need to solve `newcomer` '
                                     'labelled issues first.')
        m_assign.assert_not_called()

    @patch.object(GitLabUser, 'username', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'add_comment')
    @patch.object(GitLabIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabRepository, 'filter_issues')
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assign')
    def test_gitlab_correct_difficulty_order(self, m_assign, m_body, m_author,
                                             m_repo_issues, m_assignees,
                                             m_labels, m_comment, m_username):
        m_labels.return_value = {'low'}
        m_body.return_value = '@gitmate-bot assign'
        m_repo_issues.return_value = {
            GitLabIssue(self.gl_repo.token, self.gl_repo.full_name, 1),
            GitLabIssue(self.gl_repo.token, self.gl_repo.full_name, 2)
        }
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        m_assignees.return_value = set()
        m_username.return_value = 'sils'
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gl_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_assign.assert_called_once()

    @patch.object(GitLabUser, 'username', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'add_comment')
    @patch.object(GitLabIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabOrganization, 'filter_issues')
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assign')
    def test_gitlab_org_max_labelled_issues(self, m_assign, m_body, m_author,
                                            m_org_issues, m_assignees,
                                            m_labels, m_comment, m_username):
        self.gl_repo.settings = [
            {
                'name': 'issue_assigner',
                'settings': {
                    'enable_assign_request': True,
                    'label_numbers': {
                        'difficulty/newcomer': 1
                    },
                    'org_level': True
                }
            }
        ]
        m_labels.return_value = {'difficulty/newcomer'}
        m_body.return_value = '@gitmate-bot assign'
        m_assignees.return_value = set()
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        m_username.return_value = 'sils'
        m_org_issues.return_value = {
            GitLabIssue(self.gl_repo.token, self.gl_repo.full_name, 1),
        }
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gl_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@sils You have crossed limit of working'
                                     ' on `difficulty/newcomer` labelled '
                                     'issues.')
        m_assign.assert_not_called()

    @patch.object(GitLabUser, 'username', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'add_comment')
    @patch.object(GitLabIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assignees', new_callable=PropertyMock)
    @patch.object(GitLabOrganization, 'filter_issues')
    @patch.object(GitLabComment, 'author', new_callable=PropertyMock)
    @patch.object(GitLabComment, 'body', new_callable=PropertyMock)
    @patch.object(GitLabIssue, 'assign')
    def test_gitlab_org_difficulty_order(self, m_assign, m_body, m_author,
                                         m_org_issues, m_assignees,
                                         m_labels, m_comment, m_username):
        self.gl_repo.settings = [
            {
                'name': 'issue_assigner',
                'settings': {
                    'enable_assign_request': True,
                    'difficulty_order': ['newcomer', 'low'],
                    'org_level': True
                }
            }
        ]
        m_labels.return_value = {'low'}
        m_assignees.return_value = set()
        m_body.return_value = '@gitmate-bot assign'
        m_org_issues.return_value = set()
        m_author.return_value = GitLabUser(self.gl_repo.token, 1)
        m_username.return_value = 'sils'
        response = self.simulate_gitlab_webhook_call('Note Hook',
                                                     self.gl_comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_comment.assert_called_with(f'@sils You need to solve `newcomer` '
                                     'labelled issues first.')
        m_assign.assert_not_called()

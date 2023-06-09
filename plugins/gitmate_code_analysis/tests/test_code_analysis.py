from collections import namedtuple
import json
from os import environ
import subprocess
from unittest.mock import patch
from unittest.mock import PropertyMock

from gitmate_config.tests.test_base import GitmateTestCase
from gitmate_config.tests.test_base import StreamMock
from IGitt.GitHub.GitHubCommit import GitHubCommit
from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest
from IGitt.GitLab.GitLabCommit import GitLabCommit
from IGitt.GitLab.GitLabMergeRequest import GitLabMergeRequest
from rest_framework.status import HTTP_200_OK


PopenResult = namedtuple('ret', 'stdout stdin wait')


def popen_coala():
    return PopenResult(
        StreamMock('{"file_dicts": {}, "results": {}}'),
        StreamMock(''),
        lambda *args, **kwargs: None
    )


def fake_fetch(url: str, req_type: str, token: str,
               data: dict = None, query_params: dict = None,
               headers: dict = frozenset()):
    if '/repository/commits' in url:
        return {
            'sha': 'deadbeef',
            'id': 'deadbeef',
        }
    if '/commits' in url:
        return [{
            'sha': 'deadbeef',
            'id': 'deadbeef',
        }]
    elif '/pulls/' in url or '/issues/' in url or '/merge_requests/' in url:
        return {
            'head': {
                'sha': 'deadbeef',
                'repo': {
                    'full_name': environ['GITHUB_TEST_REPO']
                }
            },
            'base': {
                'sha': 'deadbeef',
            },
            'source_branch': 'source',
            'target_branch': 'target',
            'source_project_id': 49558751,
        }
    elif '/projects' in url:
        return {
            'http_url_to_repo':
                f'https://gitlab.com/{environ["GITHUB_TEST_REPO"]}',
            'path_with_namespace': environ['GITHUB_TEST_REPO']
        }
    else:
        return {
            'full_name': environ['GITHUB_TEST_REPO'],
            'clone_url': 'somewhere'
        }


@patch('IGitt.Interfaces._fetch', side_effect=fake_fetch)
class TestCodeAnalysis(GitmateTestCase):

    BOUNCER_INPUT = '{"old_files": {}, "new_files": {}, ' \
                    '"old_results": {}, "new_results": {}}'

    def setUp(self):
        self.setUpWithPlugin('code_analysis')

        self.github_data = {
            'repository': {'full_name': self.repo.full_name, 'id': 49558751},
            'pull_request': {'number': 0},
            'action': 'opened'
        }

        self.gitlab_data = {
            'object_attributes': {
                'target': {'path_with_namespace': environ['GITLAB_TEST_REPO']},
                'action': 'open',
                'oldrev': 'gitmatesavestheday',
                'iid': 2
            }
        }

        self.old_popen = subprocess.Popen

    def tearDown(self):
        subprocess.Popen = self.old_popen

    @patch.object(GitHubCommit, 'comment')
    @patch.object(GitHubMergeRequest, 'labels', new_callable=PropertyMock)
    def test_pr_analysis_no_issues_github(
        self, labels_mock, comment_mock, _, pr_based=False
    ):
        self.repo.settings = [
            {
                'name': 'code_analysis',
                'settings': {
                    'pr_based_analysis': pr_based,
                }
            }
        ]

        def popen_bouncer():
            return PopenResult(
                StreamMock('{}'),
                StreamMock(self.BOUNCER_INPUT),
                lambda *args, **kwargs: None
            )

        def fake_popen(cmd, **kwargs):
            if 'bouncer.py' in cmd:
                return popen_bouncer()

            assert 'run.py' in cmd
            return popen_coala()

        labels_mock.return_value = {'process/pending_review'}
        subprocess.Popen = fake_popen

        response = self.simulate_github_webhook_call(
            'pull_request', self.github_data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        comment_mock.assert_not_called()
        labels_mock.assert_called_with({'process/pending_review'})

    def test_pr_analysis_no_issues_pr_based_github(self, *args):
        return self.test_pr_analysis_no_issues_github(pr_based=True)

    @patch.object(GitHubCommit, 'comment')
    @patch.object(GitHubMergeRequest, 'labels', new_callable=PropertyMock)
    def test_pr_analysis_issues_github(self, labels_mock, comment_mock, _):
        def fake_popen(cmd, **kwargs):
            if 'bouncer.py' in cmd:
                return popen_bouncer()

            assert 'run.py' in cmd
            return popen_coala()

        def popen_bouncer():
            return PopenResult(
                StreamMock(
                    json.dumps({
                        'section': [
                            {
                                'message': 'a message',
                                'origin': 'I come from here',
                                'diffs': None,
                            },
                            {
                                'message': 'a message',
                                'origin': 'I come from here',
                                'affected_code': [
                                    {
                                        'start': {
                                            'file': 'filename',
                                            'line': 1
                                        }
                                    },
                                ],
                                'diffs': {
                                    'filename': 'unified diff here',
                                },
                            }
                        ]
                    })
                ),
                StreamMock(self.BOUNCER_INPUT),
                lambda *args, **kwargs: None
            )

        labels_mock.return_value = {'process/pending_review'}
        subprocess.Popen = fake_popen
        response = self.simulate_github_webhook_call(
            'pull_request', self.github_data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        assert comment_mock.call_count == 2
        labels_mock.assert_called_with({'process/WIP'})

    @patch.object(GitHubCommit, 'comment')
    @patch.object(GitHubMergeRequest, 'labels', new_callable=PropertyMock)
    def test_pr_analysis_many_issues_github(
        self, labels_mock, comment_mock, _
    ):
        self.repo.settings = [
            {
                'name': 'code_analysis',
                'settings': {
                    'pr_based_analysis': False,
                }
            }
        ]

        def fake_popen(cmd, **kwargs):
            if 'bouncer.py' in cmd:
                return popen_bouncer()

            assert 'run.py' in cmd
            return popen_coala()

        def popen_bouncer():
            return PopenResult(
                StreamMock(
                    json.dumps({
                        'too_many': [
                            {
                                'message': 'message ' + str(i),
                                'origin': 'I come from here'
                            }
                            for i in range(12)
                        ]
                    })
                ),
                StreamMock(self.BOUNCER_INPUT),
                lambda *args, **kwargs: None
            )

        labels_mock.return_value = {'process/pending_review'}
        subprocess.Popen = fake_popen
        response = self.simulate_github_webhook_call(
            'pull_request', self.github_data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        # More than three results, one summary comment
        comment_mock.assert_called_once()
        labels_mock.assert_called_with({'process/WIP'})

    @patch.object(GitLabCommit, 'comment')
    @patch.object(GitLabMergeRequest, 'labels', new_callable=PropertyMock)
    def test_pr_analysis_no_issues_gitlab(
        self, labels_mock, comment_mock, _, pr_based=False
    ):
        self.repo.settings = [
            {
                'name': 'code_analysis',
                'settings': {
                    'pr_based_analysis': pr_based,
                }
            }
        ]

        def popen_bouncer():
            return PopenResult(
                StreamMock('{}'),
                StreamMock(self.BOUNCER_INPUT),
                lambda *args, **kwargs: None
            )

        def fake_popen(cmd, **kwargs):
            if 'bouncer.py' in cmd:
                return popen_bouncer()

            assert 'run.py' in cmd
            return popen_coala()

        labels_mock.return_value = {'process/pending_review'}
        subprocess.Popen = fake_popen
        response = self.simulate_gitlab_webhook_call(
            'Merge Request Hook', self.gitlab_data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        comment_mock.assert_not_called()
        labels_mock.assert_called_with({'process/pending_review'})

    def test_pr_analysis_no_issues_pr_based_gitlab(self, *args):
        return self.test_pr_analysis_no_issues_gitlab(pr_based=True)

    @patch.object(GitLabCommit, 'comment')
    @patch.object(GitLabMergeRequest, 'labels', new_callable=PropertyMock)
    def test_pr_analysis_issues_gitlab(self, labels_mock, comment_mock, _):
        def fake_popen(cmd, **kwargs):
            if 'bouncer.py' in cmd:
                return popen_bouncer()

            assert 'run.py' in cmd
            return popen_coala()

        def popen_bouncer():
            return PopenResult(
                StreamMock(
                    json.dumps({
                        'section': [
                            {
                                'message': 'a message',
                                'origin': 'I come from here',
                                'diffs': None,
                            },
                            {
                                'message': 'a message',
                                'origin': 'I come from here',
                                'affected_code': [
                                    {
                                        'start': {
                                            'file': 'filename',
                                            'line': 1
                                        }
                                    },
                                ],
                                'diffs': {
                                    'filename': 'unified diff here',
                                },
                            }
                        ]
                    })
                ),
                StreamMock(self.BOUNCER_INPUT),
                lambda *args, **kwargs: None
            )

        labels_mock.return_value = {'process/pending_review'}
        subprocess.Popen = fake_popen
        response = self.simulate_gitlab_webhook_call(
            'Merge Request Hook', self.gitlab_data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        assert comment_mock.call_count == 2
        labels_mock.assert_called_with({'process/WIP'})

    @patch.object(GitLabCommit, 'comment')
    @patch.object(GitLabMergeRequest, 'labels', new_callable=PropertyMock)
    def test_pr_analysis_many_issues_gitlab(
        self, labels_mock, comment_mock, _
    ):
        self.repo.settings = [
            {
                'name': 'code_analysis',
                'settings': {
                    'pr_based_analysis': False,
                }
            }
        ]

        def fake_popen(cmd, **kwargs):
            if 'bouncer.py' in cmd:
                return popen_bouncer()

            assert 'run.py' in cmd
            return popen_coala()

        def popen_bouncer():
            return PopenResult(
                StreamMock(
                    json.dumps({
                        'too_many': [
                            {
                                'message': 'message ' + str(i),
                                'origin': 'I come from here'
                            }
                            for i in range(12)
                        ]
                    })
                ),
                StreamMock(self.BOUNCER_INPUT),
                lambda *args, **kwargs: None
            )

        labels_mock.return_value = {'process/pending_review'}
        subprocess.Popen = fake_popen
        response = self.simulate_gitlab_webhook_call(
            'Merge Request Hook', self.gitlab_data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        # More than three results, one summary comment
        comment_mock.assert_called_once()
        labels_mock.assert_called_with({'process/WIP'})

from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import PropertyMock
import attr
import bugspots
import shutil
from IGitt.GitHub.GitHubIssue import GitHubIssue
from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest
from IGitt.GitHub.GitHubRepository import GitHubRepository
from rest_framework import status

from gitmate_config.tests.test_base import GitmateTestCase


def generate_fake_bugspots(hotspot_files):
    @attr.s
    class BugspotsResult:
        filename = attr.ib(convert=str)

    class FakeBugspots:
        def __init__(self, *args, **kwargs):
            pass

        def get_hotspots(self):
            return [BugspotsResult(file) for file in hotspot_files]

    return FakeBugspots


class TestBugSpotter(GitmateTestCase):

    def setUp(self):
        self.setUpWithPlugin('bug_spotter')

        self.hook_data = {
            'repository': {'full_name': self.repo.full_name},
            'pull_request': {'number': 7},
            'action': 'synchronize'
        }

        self.addCleanup(lambda: setattr(shutil, 'rmtree', shutil.rmtree))
        shutil.rmtree = lambda *args, **kwargs: None

    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubRepository, 'get_clone', autospec=True)
    @patch.object(GitHubMergeRequest, 'affected_files',
                  new_callable=PropertyMock)
    def test_risky(self, m_aff_files, m_clone, m_labels):
        m_aff_files.return_value = {'file1', 'file2'}
        m_clone.return_value = None, '/path/doesnt/exist/nowhere'
        m_labels.return_value.__ior__ = MagicMock()

        bugspots.Bugspots = generate_fake_bugspots({'file1'})

        response = self.simulate_github_webhook_call(
            'pull_request', self.hook_data)

        m_clone.assert_called()
        m_labels.assert_called()

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        m_labels().__ior__.assert_called_with({'review carefully!'})

    @patch.object(GitHubIssue, 'labels', new_callable=PropertyMock)
    @patch.object(GitHubRepository, 'get_clone', autospec=True)
    @patch.object(GitHubMergeRequest, 'affected_files',
                  new_callable=PropertyMock)
    def test_not_risky(self, m_aff_files, m_clone, m_labels):
        m_aff_files.return_value = {'file1', 'file2'}
        m_clone.return_value = None, '/path/doesnt/exist/nowhere'
        m_labels.return_value.add = MagicMock()

        bugspots.Bugspots = generate_fake_bugspots({'another_file'})

        response = self.simulate_github_webhook_call(
            'pull_request', self.hook_data)

        m_clone.assert_called()
        m_labels.assert_not_called()

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        m_labels().add.assert_not_called()

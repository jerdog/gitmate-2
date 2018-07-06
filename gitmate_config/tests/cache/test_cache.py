from os import environ
import json

from django.core.cache import cache
from IGitt.GitHub.GitHubRepository import GitHubRepository
from IGitt.GitHub import GitHubToken

from gitmate_config.tests.test_base import RecordedTestCase


class CacheTestCase(RecordedTestCase):
    def setUp(self):
        self.token = GitHubToken(environ['GITHUB_TEST_TOKEN'])
        self.repo = GitHubRepository(self.token, environ['GITHUB_TEST_REPO'])

    def test_igitt_integration(self):
        self.assertIsNone(cache.get(self.repo.url))

        self.repo.refresh()
        old_entry = json.loads(cache.get(self.repo.url))
        self.assertIsNotNone(old_entry)

        self.repo.refresh()
        new_entry = json.loads(cache.get(self.repo.url))
        self.assertIsNotNone(new_entry)

        self.assertEquals(new_entry['lastFetched'], old_entry['lastFetched'])

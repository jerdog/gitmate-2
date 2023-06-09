from unittest.mock import patch
from unittest.mock import PropertyMock

from IGitt.GitHub.GitHubComment import GitHubComment
from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest
from IGitt.Interfaces.Comment import CommentType
from IGitt.Interfaces.Actions import MergeRequestActions

from gitmate_config.tests.test_base import GitmateTestCase
from gitmate_hooks.utils import run_plugin_for_all_repos
from gitmate_hooks.utils import ResponderRegistrar


class TestResponderRegistrar(GitmateTestCase):

    def setUp(self):
        super().setUpWithPlugin('testplugin')

        @ResponderRegistrar.responder(self.plugin,
                                      MergeRequestActions.OPENED)
        def test_responder(_, example_bool_setting: bool = True):
            return example_bool_setting

        @ResponderRegistrar.scheduled_responder(
            self.plugin, 100.00, is_active=True)
        def scheduled_responder_function(_, example_bool_setting: bool = True):
            return example_bool_setting

    @patch.object(GitHubComment, 'body', new_callable=PropertyMock)
    def test_blocked_comment_response(self, m_body):

        @ResponderRegistrar.responder(self.plugin,
                                      MergeRequestActions.COMMENTED)
        def test_blocked_responder(_, comment, *args, **kwargs):
            # this should never run
            return comment.body  # pragma: no cover

        mr = GitHubMergeRequest(None, 'test/1', 0)
        comment = GitHubComment(None, 'test/1', CommentType.MERGE_REQUEST, 0)
        m_body.return_value = ('Hello\n'
                               '(Powered by [GitMate.io](https://gitmate.io))')

        # ensures that the event was blocked, if it weren't it will return the
        # comment body.
        self.assertEqual(
            [result.get() for result in ResponderRegistrar.respond(
                MergeRequestActions.COMMENTED, mr, comment, repo=self.repo)],
            []
        )

    def test_active_plugin(self):
        self.assertEqual(
            [result.get() for result in ResponderRegistrar.respond(
                MergeRequestActions.OPENED, self.plugin, repo=self.repo)],
            [True]
        )
        self.repo.settings = [{
            'name': 'testplugin',
            'settings': {
                'example_bool_setting': False
            }
        }]
        self.assertEqual(
            [result.get() for result in ResponderRegistrar.respond(
                MergeRequestActions.OPENED, self.plugin, repo=self.repo)],
            [False]
        )

    def test_active_plugin_scheduled_responder(self):
        self.assertEqual(
            [result.get() for result in ResponderRegistrar.respond(
                'testplugin.scheduled_responder_function',
                self.repo.igitt_repo,
                repo=self.repo)],
            [True, True]
        )

    @patch.object(ResponderRegistrar, 'respond', return_value=None)
    def test_run_plugin_for_all_repos(self, m_respond):
        run_plugin_for_all_repos(self.plugin,
                                 'testplugin.scheduled_responder_function',
                                 True)
        self.assertEqual(m_respond.call_count, 2)

    def test_inactive_plugin(self):
        # Clearing all plugins!
        self.repo.plugins = []
        self.repo.save()

        self.assertEqual(
            [result.get() for result in ResponderRegistrar.respond(
                MergeRequestActions.OPENED, self.plugin, repo=self.repo)],
            []
        )

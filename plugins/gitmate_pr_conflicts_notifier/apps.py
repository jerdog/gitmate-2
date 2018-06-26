
from gitmate.enums import PluginCategory
from gitmate.utils import GitmatePluginConfig


class GitmatePrConflictsNotifierConfig(GitmatePluginConfig):
    name = 'plugins.gitmate_pr_conflicts_notifier'
    verbose_name = 'Notify merge conflicts in a PR'
    plugin_category = PluginCategory.PULLS
    description = ('Marks label and comments a help message on new and updated'
                   ' PRs which have merge conflicts')

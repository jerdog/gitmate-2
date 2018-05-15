from gitmate.enums import PluginCategory
from gitmate.utils import GitmatePluginConfig


class GitmatePrRejectorConfig(GitmatePluginConfig):
    name = 'plugins.gitmate_pr_rejector'
    verbose_name = "Reject PR's opened on certain source branch"
    plugin_category = PluginCategory.PULLS
    description = 'Close PR if it is opened on specified source branch'

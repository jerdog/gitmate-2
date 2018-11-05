
from gitmate.enums import PluginCategory
from gitmate.utils import GitmatePluginConfig


class GitmateScrumConfig(GitmatePluginConfig):
    name = 'plugins.gitmate_scrum'
    verbose_name = 'A scrum lifecyle plugin'
    plugin_category = PluginCategory.ANALYSIS
    description = 'Manages the various life cycle states in scrum development.'

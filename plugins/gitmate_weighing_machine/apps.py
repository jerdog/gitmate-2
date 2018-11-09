from gitmate.enums import PluginCategory
from gitmate.utils import GitmatePluginConfig


class GitmateWeighingMachineConfig(GitmatePluginConfig):
    name = 'plugins.gitmate_weighing_machine'
    verbose_name = 'Check issue weights'
    plugin_category = PluginCategory.ISSUE
    description = ('Verifies presence of weights on issues and checks the'
                   'range of weights, if present.')

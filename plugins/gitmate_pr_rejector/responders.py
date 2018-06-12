import re

from IGitt.Interfaces.Actions import MergeRequestActions
from IGitt.Interfaces.MergeRequest import MergeRequest
from IGitt.Interfaces import MergeRequestStates

from gitmate_hooks.utils import ResponderRegistrar


@ResponderRegistrar.responder(
    'pr_rejector',
    MergeRequestActions.OPENED,
    MergeRequestActions.SYNCHRONIZED
)
def reject_pull_requests(pr: MergeRequest,
                         branch_names: list = ['master'],
                         message: str = 'Open PR on a different source branch '
                         'other than master.'):
    for branch in branch_names:
        if (re.fullmatch(branch, pr.head_branch_name) and
                pr.state == MergeRequestStates.OPEN):
            pr.add_comment(message)
            pr.close()

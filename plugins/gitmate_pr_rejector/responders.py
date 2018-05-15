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

    if pr.head_branch_name in branch_names:
        if pr.state == MergeRequestStates.OPEN:
            pr.add_comment(message)
            pr.close()

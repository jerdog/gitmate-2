from IGitt.Interfaces.Actions import MergeRequestActions
from IGitt.Interfaces.MergeRequest import MergeRequest

from gitmate.utils import lock_igitt_object
from gitmate_hooks.utils import ResponderRegistrar


@ResponderRegistrar.responder(
    'pr_conflicts_notifier',
    MergeRequestActions.OPENED,
    MergeRequestActions.SYNCHRONIZED
)
def notify_merge_conflicts(
    pr: MergeRequest,
    conflicts_label: str='rebase',
    conflicts_message: str='Resolve conflicts message'
):
    """
    Check the pull request for merge conflicts, if pull request has merge
    conflicts, mark PR with conflict label and comment a help message.
    """
    with lock_igitt_object('label mr', pr):
        labels = pr.labels
        if pr.mergeable:
            labels.discard(conflicts_label)
        else:
            labels.add(conflicts_label)
            pr.add_comment(conflicts_message)
        pr.labels = labels

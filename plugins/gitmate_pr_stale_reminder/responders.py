from datetime import datetime
from datetime import timedelta
from celery.schedules import crontab
from IGitt.Interfaces.Actions import MergeRequestActions
from IGitt.Interfaces.MergeRequest import MergeRequest, MergeRequestStates
from IGitt.Interfaces.Repository import Repository

from gitmate.utils import lock_igitt_object
from gitmate_hooks.utils import ResponderRegistrar


@ResponderRegistrar.scheduled_responder(
    'pr_stale_reminder', crontab(minute='0', hour='6,18'), is_active=True)
def add_stale_label_to_merge_requests(
        repo: Repository,
        pr_expire_limit: int = 'Expiry limit in no. of day for pull requests',
        stale_label: str = 'Label to be used for marking stale'
):
    """
    Assigns the chosen label to pull requests which haven't been updated in a
    certain period of time.
    """
    minimum_pr_update_time = (datetime.now() -
                              timedelta(days=pr_expire_limit)).date()
    for pr in repo.search_mrs(
            updated_before=minimum_pr_update_time,
            state=MergeRequestStates.OPEN,
    ):
        with lock_igitt_object('label mr', pr):
            if stale_label not in pr.labels:
                pr.labels = pr.labels | {stale_label}


@ResponderRegistrar.responder(
    'pr_stale_reminder',
    MergeRequestActions.LABELED,
    MergeRequestActions.UNLABELED,
    MergeRequestActions.REOPENED,
    MergeRequestActions.SYNCHRONIZED,
    MergeRequestActions.COMMENTED,
    MergeRequestActions.ATTRIBUTES_CHANGED,
    MergeRequestActions.MERGED
)
def remove_stale_label_from_merge_requests(
        pr: MergeRequest,
        *args,
        stale_label: str = 'Label to be used for marking stale'
):
    """
    Unassigns the chosen label from pull requests when they are updated again.
    """
    if len(args) > 0 and args[0] == stale_label:
        # LABELED and UNLABELED events return the label used, skip action if
        # the label was ``stale_label``
        return

    with lock_igitt_object('label mr', pr):
        pr.labels = pr.labels - {stale_label}

from IGitt.Interfaces.Actions import MergeRequestActions
from IGitt.Interfaces.MergeRequest import MergeRequest

from gitmate.utils import lock_igitt_object
from gitmate_hooks.utils import ResponderRegistrar


@ResponderRegistrar.responder(
    'auto_label_pending_or_wip',
    MergeRequestActions.OPENED,
    MergeRequestActions.SYNCHRONIZED
)
def mark_pending_review_or_wip_accordingly(
    pr: MergeRequest,
    wip_label: str='Work in progress',
    pending_review_label: str='Review pending'
):
    """
    Labels the pull request as pending review and removes work in
    progress on every changed PR accordingly. But retains work in progress
    label, if title of the pull request begins with "wip".
    """
    with lock_igitt_object('label mr', pr):
        labels = pr.labels
        # Allows [wip] and WIP:
        if not 'wip' in pr.title.lower()[:4]:
            labels.add(pending_review_label)
            labels.discard(wip_label)
        else:
            labels.add(wip_label)
            labels.discard(pending_review_label)

        pr.labels = labels


@ResponderRegistrar.responder(
    'auto_label_pending_or_wip',
    MergeRequestActions.OPENED,
    MergeRequestActions.SYNCHRONIZED
)
def check_keywords_in_commit_messages(
    pr: MergeRequest,
    wip_label: str='Work in progress',
    pending_review_label: str='Review pending',
    enable_fixes_vs_closes: bool=False,
    bug_label: str='type/bug',
    no_bug_label_message: str='Fixes is used but issue has no bug label',
    bug_label_message: str='Closes is used but issue has bug label'
):
    """
    Label the pull request as work in progress and remove pending review label
    if fixes is used but referenced issue doesn't have any bug label or Closes
    is used but referenced issue contains bug label.
    """
    if not enable_fixes_vs_closes:
        return
    with lock_igitt_object('label mr', pr):
        labels = pr.labels
        for issue in pr.will_fix_issues:
            if bug_label not in issue.labels:
                labels.add(wip_label)
                labels.discard(pending_review_label)
                pr.add_comment(no_bug_label_message)
                break
        for issue in pr.will_close_issues:
            if bug_label in issue.labels:
                labels.add(wip_label)
                labels.discard(pending_review_label)
                pr.add_comment(bug_label_message)
                break

        pr.labels = labels

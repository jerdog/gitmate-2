from IGitt.Interfaces.Actions import IssueActions
from IGitt.Interfaces.Issue import Issue

from gitmate_hooks.utils import ResponderRegistrar


@ResponderRegistrar.responder('weighing_machine',
                              IssueActions.WEIGHT_CHANGED,
                              IssueActions.OPENED,
                              IssueActions.REOPENED)
def check_presence_of_issue_weight(issue: Issue,
                                   *args,
                                   no_weight_label: str='dev/missing-weight',
                                   check_issue_weight_presence: bool = False):
    try:
        if not check_issue_weight_presence or issue.weight is not None:
            return
        issue.labels |= {no_weight_label}
    except NotImplementedError:
        pass


@ResponderRegistrar.responder('weighing_machine',
                              IssueActions.WEIGHT_CHANGED,
                              IssueActions.OPENED,
                              IssueActions.REOPENED)
def check_for_overweight_issues(issue: Issue,
                                *args,
                                check_overweight_issues: bool=False,
                                max_issue_weight: int=4,
                                max_weight_label: str='dev/over-weight'):
    try:
        if not check_overweight_issues or issue.weight is None:
            return
        if issue.weight > max_issue_weight:
            issue.labels |= {max_weight_label}
    except NotImplementedError:
        pass

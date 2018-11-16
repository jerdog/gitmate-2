from IGitt.Interfaces.Actions import IssueActions
from IGitt.Interfaces.Issue import Issue

from gitmate_hooks.utils import ResponderRegistrar


@ResponderRegistrar.responder('weighing_machine',
                              IssueActions.WEIGHT_CHANGED,
                              IssueActions.OPENED,
                              IssueActions.REOPENED)
def check_presence_of_issue_weight(issue: Issue,
                                   *args,
                                   no_weight_label: str='weight/missing',
                                   check_issue_weight_presence: bool=False):
    if check_issue_weight_presence:
        try:
            if issue.weight is not None:
                issue.labels -= {no_weight_label}
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
                                max_weight_label: str='weight/overweight'):
    if check_overweight_issues:
        try:
            if issue.weight is not None and issue.weight > max_issue_weight:
                issue.labels |= {max_weight_label}
                return
            issue.labels -= {max_weight_label}
        except NotImplementedError:
            pass

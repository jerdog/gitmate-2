from IGitt.Interfaces.Actions import IssueActions
from IGitt.Interfaces.Actions import MergeRequestActions
from IGitt.Interfaces.Issue import Issue
from IGitt.Interfaces.MergeRequest import MergeRequest
from IGitt.Interfaces.CommitStatus import Status
from IGitt.Interfaces import IssueStates

from gitmate.utils import lock_igitt_object
from gitmate_hooks.utils import ResponderRegistrar


@ResponderRegistrar.responder('issue_assigner', IssueActions.OPENED)
def add_assignees_to_issue(
    issue: Issue,
    keywords: dict() = 'Keywords that trigger assignments',
):
    issue_summary = issue.title.lower() + ' ' + issue.description.lower()
    new_assignees = {
        assignee
        for assignee, l_keywords in keywords.items()
        for keyword in l_keywords.split(',')
        if keyword.strip() and keyword in issue_summary
    }

    with lock_igitt_object('assign issue', issue, refresh_needed=False):
        for assignee in new_assignees:
            issue.assign(assignee)


@ResponderRegistrar.responder(
    'issue_assigner',
    MergeRequestActions.OPENED,
    MergeRequestActions.SYNCHRONIZED
)
def assign_issue_on_pr_commit_mention(
    pr: MergeRequest,
    keywords: dict() = 'Keywords that trigger assignments',
    enable_auto_assign: bool = False,
    assigned_message: str = 'Already assigned issue message'
):
    if not enable_auto_assign:
        return
    unassigned_issues = set()
    assigned_issues = set()
    for commit in pr.commits:
        if commit.combined_status in [Status.SUCCESS, Status.PENDING]:
            for issue in pr.closes_issues:
                if (issue.state is IssueStates.CLOSED or
                        pr.author in issue.assignees):
                    continue
                if issue.assignees:
                    assigned_issues.add(issue.web_url)
                else:
                    unassigned_issues.add(issue)

    if assigned_issues:
        pr.add_comment(
            assigned_message.format(issues=','.join(assigned_issues)))
    for issue in unassigned_issues:
        with lock_igitt_object('assign issue', issue, refresh_needed=False):
            issue.assign(pr.author.username)

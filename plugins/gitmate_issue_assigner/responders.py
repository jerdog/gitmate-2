import re

from IGitt.Interfaces.Actions import IssueActions
from IGitt.Interfaces.Actions import MergeRequestActions
from IGitt.Interfaces.Issue import Issue
from IGitt.Interfaces.MergeRequest import MergeRequest
from IGitt.Interfaces.CommitStatus import Status
from IGitt.Interfaces import IssueStates
from IGitt.Interfaces.Comment import Comment

from gitmate.utils import lock_igitt_object
from gitmate_hooks.utils import ResponderRegistrar
from gitmate_config.models import Repository

ASSIGN_COMMAND = r'@(?:{}|gitmate-bot) ((?:un|)assign)'


def assign_issue(issue, user, blocked_labels, blocked_assignees,
                 label_numbers, difficulty_order, org_level):
    repo = issue.repository
    org = repo.top_level_org
    username = user.username
    error_message = ''
    if issue.assignees:
        if user in issue.assignees:
            error_message += ('This issue is already assigned to you.')
        else:
            error_message += ('This issue is assigned to someone '
                              'else, try to work on another issue.')
        return error_message
    for label in blocked_labels:
        if label in issue.labels:
            error_message += 'Assignment to this issue is blocked.'
            return error_message
    if username in blocked_assignees:
        error_message += 'You aren\'t allowed to get assigned to any issue.'
        return error_message
    for label, number in label_numbers.items():
        if label in issue.labels:
            if org_level:
                issues = org.filter_issues(state='all', label=label,
                                           assignee=username)
            else:
                issues = repo.filter_issues(state='all', label=label,
                                            assignee=username)
            if len(issues) >= number:
                error_message += ('You have crossed limit of working on '
                                  f'`{label}` labelled issues.')
                return error_message
    for label in difficulty_order:
        if label in issue.labels:
            for d_label in difficulty_order[:difficulty_order.index(label)+1]:
                if org_level:
                    issues = org.filter_issues(state='all', label=d_label,
                                               assignee=username)
                else:
                    issues = repo.filter_issues(state='all', label=d_label,
                                                assignee=username)
                if len(issues) < 1:
                    error_message += (f'You need to solve `{d_label}` labelled'
                                      ' issues first.')
                    return error_message
    return error_message


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


@ResponderRegistrar.responder('issue_assigner', IssueActions.COMMENTED)
def assign_or_unassign_issue_per_request(
    issue: Issue,
    comment: Comment,
    enable_assign_request: bool = False,
    blocked_labels: list() = 'status/blocked',
    blocked_assignees: list() = 'gitmate-bot',
    label_numbers: dict() = 'Max number of certain labelled issues a member '
                            'can work on',
    difficulty_order: list() = 'difficulty/newcomer,difficulty/low',
    org_level: bool = False
):
    bot_name = Repository.from_igitt_repo(issue.repository).user.username
    match = re.fullmatch(ASSIGN_COMMAND.format(bot_name), comment.body)
    user = comment.author
    username = user.username
    if (not enable_assign_request or not match):
        return
    if match.group(1) == 'unassign':
        if user in issue.assignees:
            issue.unassign(username)
        else:
            issue.add_comment(f'@{username}, You are not an assignee of this '
                              'issue.')
        return
    msg = assign_issue(issue, user, blocked_labels,
                       blocked_assignees, label_numbers, difficulty_order,
                       org_level)
    if msg:
        issue.add_comment(f'@{username} {msg}')
    else:
        with lock_igitt_object('assign issue', issue, refresh_needed=False):
            issue.assign(username)

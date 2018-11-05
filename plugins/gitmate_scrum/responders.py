from typing import Set
import re

from IGitt.Interfaces import MergeRequestStates
from IGitt.Interfaces.Actions import IssueActions
from IGitt.Interfaces.Actions import MergeRequestActions
from IGitt.Interfaces.Issue import Issue
from IGitt.Interfaces.MergeRequest import MergeRequest


from gitmate_hooks.utils import ResponderRegistrar


@ResponderRegistrar.responder('scrum', IssueActions.ASSIGNEES_CHANGED)
def mark_issue_ongoing(issue: Issue,
                       usernames: Set[str],
                       operating_namespace: str='dev',
                       ongoing_label: str='ongoing'):
    labels = issue.labels
    ns_regex = re.compile('^{}/.*$'.format(operating_namespace))
    if bool(usernames):
        labels = {label for label in labels if not ns_regex.match(label)}
        labels |= {'{}/{}'.format(operating_namespace, ongoing_label)}
    issue.labels = labels


@ResponderRegistrar.responder('scrum',
                              MergeRequestActions.MERGED,
                              MergeRequestActions.SYNCHRONIZED,
                              MergeRequestActions.OPENED,
                              MergeRequestActions.REOPENED)
def mark_as_review_or_acceptance(pr: MergeRequest,
                                 operating_namespace: str='dev',
                                 review_label: str='code-review',
                                 acceptance_label: str='acceptance-QA'):
    labels = pr.labels
    ns_regex = re.compile('^{}/.*$'.format(operating_namespace))
    qa_regex = re.compile(
        r'QA:\s+(?:#|https?:\/\/\S+\/issues\/)[1-9]\d*', re.IGNORECASE)
    new_state = (acceptance_label if pr.state == MergeRequestStates.MERGED
                 else review_label)
    if any(qa_regex.search(commit.message) for commit in pr.commits):
        labels = {label for label in labels if not ns_regex.match(label)}
        labels |= {'{}/{}'.format(operating_namespace, new_state)}
    pr.labels = labels

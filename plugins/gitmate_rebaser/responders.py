import json
import re

from django.conf import settings
from IGitt.Interfaces import AccessLevel
from IGitt.Interfaces.Actions import MergeRequestActions
from IGitt.Interfaces.Comment import Comment
from IGitt.Interfaces.MergeRequest import MergeRequest

from gitmate.utils import run_in_container
from gitmate_config.models import Repository
from gitmate_hooks.utils import ResponderRegistrar


COMMAND_REGEX = (r'@(?:{}|gitmate-bot)\s+'
                 r'((?:rebase|merge|fastforward|ff|squash\s+(.+)))')


def verify_command_access(comment: Comment, merge_admin_only: bool,
                          fastforward_admin_only: bool,
                          squash_admin_only: bool,
                          cmd: str):
    """
    Verifies if the author of comment has access to perform the operation.
    """
    perm_levels = {
        'rebase': AccessLevel.CAN_READ,
        'merge': (AccessLevel.ADMIN if merge_admin_only else
                  AccessLevel.CAN_WRITE),
        'fastforward': (AccessLevel.ADMIN if fastforward_admin_only else
                        AccessLevel.CAN_WRITE),
        'squash': (AccessLevel.ADMIN if squash_admin_only else
                   AccessLevel.CAN_WRITE)
    }
    author_perm = comment.repository.get_permission_level(comment.author)
    if author_perm.value >= perm_levels[cmd].value:
        return True
    return False


def get_matched_command(body: str, username: str):
    """
    Retrieves the matching command from the comment body.
    """
    compiled_regex = re.compile(COMMAND_REGEX.format(username), re.IGNORECASE)
    match = compiled_regex.search(body.lower())
    if match:
        return {
            'rebase': ('rebase', 'rebased', None),
            'merge': ('merge', 'merged', None),
            'fastforward': ('fastforward', 'fastforwarded', None),
            'ff': ('fastforward', 'fastforwarded', None),
            'squash': ('squash', 'squashed', match.group(2))
        }.get(match.group(1).split(' ')[0], (None, None, None))
    return None, None, None


@ResponderRegistrar.responder('rebaser', MergeRequestActions.COMMENTED)
def apply_command_on_merge_request(
        pr: MergeRequest, comment: Comment,
        enable_rebase: bool = False,
        enable_merge: bool = False,
        enable_squash: bool = False,
        enable_fastforward: bool = False,
        merge_admin_only: bool = True,
        fastforward_admin_only: bool = True,
        squash_admin_only: bool = True
):
    """
    Performs a merge, fastforward, squash or rebase of a merge request when an
    authorized user posts a command mentioning the keywords ``merge``,
    ``fastforward``/``ff``, ``squash`` or ``rebase`` respectively.

    e.g. ``@gitmate-bot rebase`` rebases the pull request with master.
    """
    username = Repository.from_igitt_repo(pr.repository).user.username
    cmd, cmd_past, message = get_matched_command(comment.body, username)
    enabled_cmd = {
        'rebase': enable_rebase,
        'merge': enable_merge,
        'fastforward': enable_fastforward,
        'squash': enable_squash,
    }.get(cmd)

    if enabled_cmd:
        if not verify_command_access(comment, merge_admin_only,
                                     fastforward_admin_only, squash_admin_only,
                                     cmd):
            pr.add_comment(
                f'Hey @{comment.author.username}, you do not have the access '
                f'to perform the {cmd} action with [GitMate.io]'
                '(https://gitmate.io). Please ask a maintainer to give you '
                'access. :warning:')
            return

        pr.add_comment(
            f'Hey! I\'m [GitMate.io](https://gitmate.io)! This pull request is'
            f' being {cmd_past} automatically. Please **DO NOT** push while '
            f'{cmd} is in progress or your changes would be lost permanently '
            ':warning:')
        head_clone_url = pr.source_repository.clone_url
        base_clone_url = pr.target_repository.clone_url
        args = (settings.REBASER_IMAGE, 'python', 'run.py', cmd,
                head_clone_url, base_clone_url, pr.head_branch_name,
                pr.base_branch_name)
        if cmd == 'squash':
            args = (*args, message)
        output = run_in_container(*args)
        output = json.loads(output)
        if output['status'] == 'success':
            pr.add_comment(
                f'Automated {cmd} with [GitMate.io](https://gitmate.io) was '
                'successful! :tada:')
        elif 'error' in output:
            # hiding oauth token for safeguarding user privacy
            error = output['error'].replace(head_clone_url,
                                            '<hidden_oauth_token>')
            error = error.replace(base_clone_url, '<hidden_oauth_token>')
            pr.add_comment(f'Automated {cmd} failed! Please {cmd} your pull '
                           'request manually via the command line.\n\n'
                           'Reason:\n```\n{}\n```'.format(error))

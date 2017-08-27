from os import environ
import json
import subprocess

from IGitt.Interfaces.Actions import MergeRequestActions
from IGitt.Interfaces.Comment import Comment
from IGitt.Interfaces.MergeRequest import MergeRequest

from gitmate_hooks import ResponderRegistrar


@ResponderRegistrar.responder('rebaser', MergeRequestActions.COMMENTED)
def rebase_merge_request(pr: MergeRequest, comment: Comment):
    """
    Rebases a merge request when a user adds a rebase comment. e.g.
    ``@gitmate-bot rebase`` within the comment body.
    """
    from gitmate_config.models import Repository

    username = Repository.from_igitt_repo(pr.repository).user.username
    body = comment.body.lower()
    if '@{}'.format(username) in body and 'rebase' in body:
        pr.add_comment(
            'Hey! This pull request is being rebased automatically. Please DO '
            'NOT push while rebase is in progress or your changes would be '
            'lost!')
        proc = subprocess.Popen(
            ['docker', 'run', '-i', '--rm', environ['REBASER_IMAGE'],
             'python', 'run.py', pr.repository.clone_url, pr.head_branch_name,
             pr.base_branch_name],
            stdout=subprocess.PIPE)
        output = json.loads(proc.stdout.read().decode('utf-8'))
        proc.wait()
        if output['status'] == 'success':
            pr.add_comment('Automated rebase was successful!')
        else:
            pr.add_comment('Automated rebase failed! Please rebase your pull '
                           'request manually via the command line.')
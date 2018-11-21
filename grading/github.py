import os
import random
import string
import subprocess

import github3 as gh3


def _call_git(*args, directory=None):
    cmd = ['git']
    cmd.extend(args)
    try:
        ret = subprocess.run(cmd,
                             cwd=directory,
                             check=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode('utf-8')
        if err:
            msg = err.split(':')[1].strip()
        else:
            msg = e.stdout.decode('utf-8')
        raise RuntimeError(msg) from e

    return ret


def fetch_student(org, course, student, directory, token=None):
    """Fetch course repository for `student` from `org`

    The repository will be cloned into a sub-directory in `directory`.

    Returns the directory in which to find the students work.
    """
    # use ssh if there is no token
    if token is None:
        fetch_command = ['git', 'clone',
                         'git@github.com:{}/{}-{}.git'.format(
                             org,
                             course,
                             student
                             )
                         ]
    else:
        fetch_command = ['git', 'clone',
                         'https://{}@github.com/{}/{}-{}.git'.format(
                             token, org, course, student,
                             )
                         ]
    subprocess.run(fetch_command,
                   cwd=directory,
                   check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return os.path.join(directory, "{}-{}".format(course, student))


def create_pr(org, repository, branch, title, token):
    """Create a Pull Request with changes from branch"""
    msg = ("Merge this Pull Request to get the material for the next "
           "assignment.")

    g = gh3.login(token=token)
    repo = g.repository(org, repository)
    repo.create_pull(title, "master", branch, msg)


def create_repo(org, repository, directory, token):
    g = gh3.login(token=token)
    organization = g.organization(org)
    title = 'Template repository for {}'.format(repository)
    organization.create_repository(repository, title)

    _call_git('remote', 'add', 'origin',
              'https://{}@github.com/{}/{}'.format(token, org, repository),
              directory=directory)
    push_to_github(directory, 'master')


def repo_changed(directory):
    """Determine if the Git repository in directory is dirty"""
    ret = _call_git('status', '--porcelain', directory=directory)
    return bool(ret.stdout)


def new_branch(directory, name=None):
    """Create a new git branch in directory"""
    if name is None:
        postfix = ''.join([random.choice(string.ascii_letters)
                           for n in range(4)])
        name = "new-material-{}".format(postfix)

    _call_git('checkout', '-b', name,
              directory=directory)

    return name


def commit_all_changes(directory, msg=None):
    if msg is None:
        raise ValueError("Commit message can not be empty.")

    _call_git('add', '*', directory=directory)
    _call_git('commit', '-a', '-m', msg,
              directory=directory)


def push_to_github(directory, branch):
    """Push `branch` back to GitHub"""
    _call_git('push', '--set-upstream', 'origin', branch,
              directory=directory)


def git_init(directory):
    """Initialize git repository"""
    _call_git('init', directory=directory)
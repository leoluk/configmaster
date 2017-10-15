import os

from sh import git


def get_last_commit_message(repository_path):
    os.chdir(repository_path)
    return str(git('log', '-1', '--format=%B', _tty_out=False)).strip()


def get_last_commit_id(repository_path):
    os.chdir(repository_path)
    return str(git('log', '-1', '--format=%H', _tty_out=False)).strip()

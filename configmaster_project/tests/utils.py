import os

from sh import git, ErrorReturnCode


def get_last_commit_message(repository_path):
    os.chdir(repository_path)
    return str(git('log', '-1', '--format=%B', _tty_out=False)).strip()


def get_last_commit_id(repository_path):
    os.chdir(repository_path)
    return str(git('log', '-1', '--format=%H', _tty_out=False)).strip()


def cleanup_repo(repository_path):
    """
    Generates a commit which deletes everything.
    """
    os.chdir(repository_path)
    try:
        git('rm', '-rf', '.')
    except ErrorReturnCode:
        pass
    else:
        git('commit', '-m', 'Clean up everything')

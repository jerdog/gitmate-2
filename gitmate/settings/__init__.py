import json
import os

import raven


def get_configuration(filepath):
    """
    Loads the configuration from the given json file into a dictionary.
    """
    if filepath is None:
        return {}
    try:
        with open(filepath, 'r') as env:
            return json.loads(env.read())
    except FileNotFoundError:
        return {}


def get_release_version(git_dir, base_dir, version_file):
    """
    Retrieves the release version from git commit sha or version file, if
    present.
    """
    release_version = 'UNKNOWN_VERSION'
    if os.path.isdir(git_dir):  # pragma: no cover
        release_version = raven.fetch_git_sha(base_dir)
    elif os.path.exists(version_file):  # pragma: no cover
        with open(version_file, 'r') as ver:
            release_version = ver.read().rstrip()
    return release_version

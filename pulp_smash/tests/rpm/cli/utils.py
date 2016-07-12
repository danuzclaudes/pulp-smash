# coding=utf-8
"""Utility functions for RPM CLI tests."""
from __future__ import unicode_literals

import subprocess

from pulp_smash import cli, config, constants, utils


_REPO_ID = None
"""The ID of the repository created by ``setUpModule``."""


def _count_langpacks(server_config, repo_id):
    """Tell how many langpack content units are in the given repository.

    :param pulp_smash.config.ServerConfig server_config: Information about the
        Pulp server being targeted.
    :param repo_id: A repository ID.
    :returns: The number of langpacks in the named repository, as an integer.
    """
    # This function could be refactored to take a third "keyword" argument. But
    # what do we do about the "rpm" word in the command below?
    keyword = 'Package Langpacks:'
    completed_proc = cli.Client(server_config).run(
        'pulp-admin rpm repo list --repo-id {} --fields content_unit_counts'
        .format(repo_id).split()
    )
    lines = [
        line for line in completed_proc.stdout.splitlines() if keyword in line
    ]
    # A "Package Langpacks: n" line is printed only if at least one unit of
    # that kind is present.
    assert len(lines) in (0, 1)
    if len(lines) == 0:
        return 0
    else:
        return int(lines[0].split(keyword)[1].strip())


def create_sync_global_repo():
    cfg = config.get_config()
    client = cli.Client(cfg)

    # log in, then create repository
    utils.pulp_admin_login(cfg)

    global _REPO_ID  # pylint:disable=global-statement
    _REPO_ID = utils.uuid4()

    client.run(
        'pulp-admin rpm repo create --repo-id {} --feed {}'
        .format(_REPO_ID, constants.RPM_FEED_URL).split()
    )

    # If setUpModule() fails, tearDownModule() isn't run. In addition, we can't
    # use addCleanup(), as it's an instance method. If this set-up procedure
    # grows, consider implementing a stack of tear-down steps instead.
    try:
        client.run(
            'pulp-admin rpm repo sync run --repo-id {}'
            .format(_REPO_ID).split()
        )
    except subprocess.CalledProcessError:
        client.run(
            'pulp-admin rpm repo delete --repo-id {}'.format(_REPO_ID).split()
        )
        raise


def destory_global_repo():
    """Delete the repository created by ``setUpModule``."""
    cli.Client(config.get_config()).run(
        'pulp-admin rpm repo delete --repo-id {}'.format(_REPO_ID).split()
    )


def get_repo_id():
    return _REPO_ID


def _get_rpm_names(server_config, repo_id):
    """Get a list of names of all packages in a repository.

    :param pulp_smash.config.ServerConfig server_config: Information about the
        Pulp server being targeted.
    :param repo_id: A RPM repository ID.
    :returns: The names of all modules in a repository, as an ``list``.
    """
    keyword = 'Name:'
    completed_proc = cli.Client(server_config).run(
        'pulp-admin rpm repo content rpm --repo-id {}'.format(repo_id).split()
    )
    return [
        line.split(keyword)[1].strip()
        for line in completed_proc.stdout.splitlines() if keyword in line
    ]

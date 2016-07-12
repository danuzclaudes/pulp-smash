# coding=utf-8
"""Tests that sync RPM repositories."""
from __future__ import unicode_literals

import random

import unittest2

from pulp_smash import cli, config
from pulp_smash.tests.rpm.utils import set_up_module
from pulp_smash.tests.rpm.cli.utils import (
    create_sync_global_repo,
    destory_global_repo,
    get_repo_id,
    _get_rpm_names,
)


def setUpModule():  # pylint:disable=invalid-name
    """Execute ``pulp-admin login`` on the target Pulp system."""
    set_up_module()
    create_sync_global_repo()


def tearDownModule():  # pylint:disable=invalid-name
    """Delete the repository created by ``setUpModule``."""
    destory_global_repo()


class RemovedContentTestCase(unittest2.TestCase):
    """Test whether Pulp can sync content into a repo after it's been removed.

    This test case targets `Pulp #1775`_ and the corresponding Pulp Smash
    issue, `Pulp Smash #243`_.

    1. Create and sync a repository. Select a content unit.
    2. Delete the content unit from the repository, and verify it's absent.
    3. Sync the repository, and verify that the content unit is present.

    .. _Pulp #1775: https://pulp.plan.io/issues/1775
    .. _Pulp Smash #243: https://github.com/PulpQE/pulp-smash/issues/243
    """
    @classmethod
    def setUpClass(cls):
        """Create and sync a repository. Select a content unit from it."""
        cls.cfg = config.get_config()
        cls.repo_id = get_repo_id()
        cls.rpm_name = random.choice(_get_rpm_names(cls.cfg, cls.repo_id))

    def test_01_remove_rpm(self):
        """Remove the selected RPM from the repository. Verify it's absent."""
        cli.Client(self.cfg).run(
            'pulp-admin rpm repo remove rpm --repo-id {} --str-eq name={}'
            .format(self.repo_id, self.rpm_name).split()
        )
        self.assertNotIn(self.rpm_name, _get_rpm_names(self.cfg, self.repo_id))

    def test_02_add_rpm(self):
        """Sync the repository. Verify the selected RPM is present."""
        completed_proc = cli.Client(self.cfg).run(
            'pulp-admin rpm repo sync run --repo-id {}'
            .format(self.repo_id).split()
        )
        with self.subTest():
            self.assertIn(self.rpm_name, _get_rpm_names(self.cfg, self.repo_id))
        phrase = 'Invalid properties:'
        for stream in ('stdout', 'stderr'):
            with self.subTest(stream=stream):
                self.assertNotIn(phrase, getattr(completed_proc, stream))

    @classmethod
    def tearDownClass(cls):
        """Delete the repository and clean up orphans."""
        cli.Client(cls.cfg).run(
            'pulp-admin rpm repo delete --repo-id {}'
            .format(cls.repo_id).split()
        )

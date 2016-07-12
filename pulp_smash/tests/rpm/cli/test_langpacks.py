# coding=utf-8
"""Tests for Pulp's langpack support."""
from __future__ import unicode_literals

import unittest2
from packaging.version import Version

from pulp_smash import cli, config, utils
from pulp_smash.tests.rpm.utils import set_up_module
from pulp_smash.tests.rpm.cli.utils import (
    _count_langpacks,
    create_sync_global_repo,
    destory_global_repo,
    get_repo_id,
)


def setUpModule():  # pylint:disable=invalid-name
    """Possibly skip tests. Create and sync an RPM repository.

    Skip tests in this module if the RPM plugin is not installed on the target
    Pulp server. Then create an RPM repository with a feed and sync it. Test
    cases may copy data from this repository but should **not** change it.
    """
    set_up_module()
    create_sync_global_repo()


def tearDownModule():  # pylint:disable=invalid-name
    """Delete the repository created by ``setUpModule``."""
    destory_global_repo()


class UploadAndRemoveLangpacksTestCase(unittest2.TestCase):
    """Test whether one can upload to and remove langpacks from a repository.

    This test targets `Pulp Smash #270`_. The test steps are as follows:

    1. Create a repository.
    2. Upload langpacks to the repository. Verify the correct number of
       langpacks are present.
    3. Remove langpacks from the repository. Verify that no langpacks are
       present.

    .. _Pulp Smash #270: https://github.com/PulpQE/pulp-smash/issues/270
    """
    @classmethod
    def setUpClass(cls):
        """Create a repository."""
        cls.cfg = config.get_config()
        if cls.cfg.version < Version('2.9'):
            raise unittest2.SkipTest('This test requires Pulp 2.9 or greater.')
        cls.client = cli.Client(cls.cfg)
        cls.repo_id = get_repo_id()

    def test_01_upload_langpacks(self):
        """Upload a langpack to the repository."""
        cmd = (
            'pulp-admin rpm repo uploads langpacks --repo-id {0} '
            '--name {1} --install {1}-%s'
        ).format(self.repo_id, utils.uuid4()).split()
        self.client.run(cmd)
        num_langpacks = _count_langpacks(self.cfg, self.repo_id)
        self.assertEqual(num_langpacks, 1, cmd)

    def test_02_remove_langpacks(self):
        """Remove all langpacks from the repository."""
        cmd = (
            'pulp-admin rpm repo remove langpacks --repo-id {0} '
            '--str-eq repo_id={0}'
        ).format(self.repo_id).split()
        self.client.run(cmd)
        package_counts = _count_langpacks(self.cfg, self.repo_id)
        self.assertEqual(package_counts, 0, cmd)

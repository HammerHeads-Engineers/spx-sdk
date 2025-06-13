# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch

from spx_sdk.registry import install_requirements_from_dir


class TestInstallRequirementsFromDir(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory.
        self.test_dir = tempfile.mkdtemp()
        # Create a sample requirements file (matches default pattern "requirements*.txt")
        self.req_file = os.path.join(self.test_dir, "requirements.txt")
        with open(self.req_file, "w", encoding="utf-8") as f:
            f.write("requests==2.25.1\n")

    def tearDown(self):
        # Clean up the temporary directory.
        shutil.rmtree(self.test_dir)
        # Remove PIP_INDEX_URL from environment if it was set.
        os.environ.pop("PIP_INDEX_URL", None)

    @patch("subprocess.check_call")
    def test_install_requirements_basic(self, mock_check_call):
        # Ensure that, without PIP_INDEX_URL set, the function calls pip install with the expected command.
        os.environ.pop("PIP_INDEX_URL", None)
        install_requirements_from_dir(self.test_dir, requirements_pattern="requirements*.txt")

        expected_cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "-r",
            self.req_file
        ]
        mock_check_call.assert_called_once_with(expected_cmd)

    @patch("subprocess.check_call")
    def test_install_requirements_with_index(self, mock_check_call):
        # Test that the function extends the pip install command when PIP_INDEX_URL is provided.
        os.environ["PIP_INDEX_URL"] = "https://my.private.repo/simple"
        install_requirements_from_dir(self.test_dir, requirements_pattern="requirements*.txt")

        expected_cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "-r",
            self.req_file,
            "--index-url",
            "https://my.private.repo/simple"
        ]
        mock_check_call.assert_called_once_with(expected_cmd)

    @patch("subprocess.check_call")
    def test_no_requirements_file(self, mock_check_call):
        # If there is no file matching the requirements pattern, subprocess.check_call should not be called.
        os.remove(self.req_file)
        install_requirements_from_dir(self.test_dir, requirements_pattern="requirements*.txt")
        mock_check_call.assert_not_called()


if __name__ == '__main__':
    unittest.main()

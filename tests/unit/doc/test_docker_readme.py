# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from docutils import frontend
from docutils import nodes
from docutils.parsers import rst
from docutils import utils
import os
import re
import sys
from unittest import mock

import rally_openstack
from tests.unit import test


ROOT_DIR = os.path.dirname(os.path.dirname(rally_openstack.__file__))


class DockerReadmeTestCase(test.TestCase):
    RE_RELEASE = re.compile(r"\[(?P<version>[0-9]+\.[0-9]+.[0-9]+)\]")

    def get_releases(self):
        full_path = os.path.join(ROOT_DIR, "CHANGELOG.rst")
        with open(full_path) as f:
            changelog = f.read()
        with mock.patch.object(sys, "stderr"):
            parser = rst.Parser()
            settings = frontend.OptionParser(
                components=(rst.Parser,)).get_default_values()
            document = utils.new_document(changelog, settings)
            parser.parse(changelog, document)
            changelog = document.children
        if len(changelog) != 1:
            self.fail("'%s' file should contain one global section "
                      "with subsections for each release." % full_path)

        releases = []
        for node in changelog[0].children:
            if not isinstance(node, nodes.section):
                continue
            title = node.astext().split("\n", 1)[0]
            result = self.RE_RELEASE.match(title)
            if result:
                releases.append(result.groupdict()["version"])
        if not releases:
            self.fail("'%s' doesn't mention any releases..." % full_path)
        return releases

    def test_mentioned_latest_version(self):
        full_path = os.path.join(ROOT_DIR, "DOCKER_README.md")
        with open(full_path) as f:
            readme = f.read()

        releases = self.get_releases()
        latest_release = releases[0]
        previous_release = releases[1]
        print("All discovered releases: %s" % ", ".join(releases))

        found = False
        for i, line in enumerate(readme.split("\n"), 1):
            if latest_release in line:
                found = True
            elif previous_release in line:
                self.fail(
                    "You need to change %s to %s in all places where the "
                    "latest release is mentioned."
                    "\n  Filename: %s"
                    "\n  Line Number: %s"
                    "\n  Line:  %s" %
                    (previous_release, latest_release, full_path, i, line))

        if not found:
            self.fail("No latest nor previous release is found at README file "
                      "for our Docker image. It looks like the format of it "
                      "had changed. Please adopt the current test suite.")

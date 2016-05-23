import os
import subprocess
import tempfile
from tempfile import mkdtemp

from os.path import join

import sys
from time import sleep

from scrapy.utils.python import to_native_str
from scrapy.utils.test import get_testenv
from shutil import rmtree
from twisted.trial import unittest


class ProjectTest(unittest.TestCase):
    project_name = 'testproject'

    def setUp(self):
        self.temp_path = mkdtemp()
        self.cwd = self.temp_path
        self.proj_path = join(self.temp_path, self.project_name)
        self.proj_mod_path = join(self.proj_path, self.project_name)
        self.env = get_testenv()

        self.call('startproject', self.project_name)
        self.cwd = join(self.temp_path, self.project_name)
        os.chdir(self.cwd)
        self.env['SCRAPY_SETTINGS_MODULE'] = '%s.settings' % self.project_name
        self.external_path = join(self.cwd, 'external.json')
        with open(self.external_path, 'w') as external:
            external.write('''
[
  {
    "name": "PythonSpider",
    "command": "scripts/dmoz.py"
  },

  {
    "name": "JavaSpider",
    "command": "java",
    "args": ["MyClass"]
  }
]
''')

    def tearDown(self):
        rmtree(self.temp_path)

    def call(self, *new_args, **kwargs):
        with tempfile.NamedTemporaryFile() as out:
            args = (sys.executable, '-m', 'scrapy.cmdline') + new_args
            return subprocess.call(args, stdout=out, stderr=out, cwd=self.cwd,
                env=self.env, **kwargs)

    def proc(self, *new_args, **kwargs):
        args = (sys.executable, '-m', 'scrapy.cmdline') + new_args
        p = subprocess.Popen(args, cwd=self.cwd, env=self.env,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             **kwargs)

        waited = 0
        interval = 0.2
        while p.poll() is None:
            sleep(interval)
            waited += interval
            if waited > 15:
                p.kill()
                assert False, 'Command took too much time to complete'

        return p


class ListCommandTest(ProjectTest):

    def test_list_is_running(self):
        self.assertEqual(0, self.call('list'))

    def test_external_spiders(self):
        p = self.proc('list')
        out = to_native_str(p.stdout.read())

        self.assertIn("JavaSpider", out)
        self.assertIn("PythonSpider", out)
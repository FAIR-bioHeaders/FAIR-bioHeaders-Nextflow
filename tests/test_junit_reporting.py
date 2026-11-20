# SPDX-License-Identifier: MPL-2.0
"""JUnit accounting controls independent of converter execution."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('composition', Path(__file__).with_name('run.py'))
composition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(composition)


class JunitReportingTests(unittest.TestCase):
    def totals(self, xml):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'junit.xml'
            report.write_text(xml)
            return composition.junit_totals(report)

    def test_nested_cases_are_counted_once(self):
        self.assertEqual(self.totals('''<testsuites><testsuite tests="5" failures="1" errors="1" skipped="1">
          <testcase/><testsuite tests="4" failures="1" errors="1" skipped="1">
          <testcase/><testcase><skipped/></testcase><testcase><failure/></testcase>
          <testcase><error/></testcase></testsuite></testsuite></testsuites>'''), (5, 1, 1, 1))

    def test_nested_summary_aggregates_are_not_double_counted(self):
        self.assertEqual(self.totals('''<testsuites><testsuite tests="5" failures="1" errors="1" skipped="1">
          <testsuite tests="4" failures="1" errors="1" skipped="1"/>
          <testsuite tests="1"/></testsuite></testsuites>'''), (5, 1, 1, 1))

    def test_all_skipped_is_not_all_passed(self):
        total, failures, errors, skipped = self.totals('''<testsuite tests="2" skipped="2">
          <testcase><skipped/></testcase><testcase><skipped/></testcase></testsuite>''')
        self.assertEqual((total - failures - errors - skipped, skipped), (0, 2))

    def test_empty_and_summary_only_reports(self):
        self.assertEqual(self.totals('<testsuites><testsuite tests="0"/></testsuites>'), (0, 0, 0, 0))
        self.assertEqual(self.totals('<testsuite tests="4" failures="1" errors="1" skipped="1"/>'), (4, 1, 1, 1))


if __name__ == '__main__':
    unittest.main()

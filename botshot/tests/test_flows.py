from unittest import TestCase

import yaml

from botshot.core.flow import Flow


class TestFlows(TestCase):

    def setUp(self):
        self.flow = yaml.load("""
        default:
            intent: "(default.*)"
            states:
            - name: root
              action:
                text: "Hello, world!"
                next: "default.next"
            - name: next
        """)

    def test_import_flow(self):
        flow = Flow.load("default", self.flow['default'], relpath="botshot.tests")
        self.assertEqual(flow.name, "default")
        self.assertEqual(flow.intent, "(default.*)")
        self.assertIn("root", flow.states)

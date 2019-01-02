import pytest
import yaml

from botshot.core.flow import Flow


class TestFlows():

    flow = yaml.load("""
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
        assert flow.name == "default"
        assert flow.intent == "(default.*)"
        assert "root" in flow.states
        assert flow.matches_intent("default")
        assert not flow.matches_intent("deflate")

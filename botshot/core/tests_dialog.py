import unittest


TEST_YAML = """
default:
  intent: "(default|greeting)"
  states:

  - name: 'root'
    action: "botshot.core.tests_dialog.foo_action"
    require:
    - slot: WHEN
      entity: datetime
      action:
        text: When?
    - slot: FROM
      action: "botshot.core.tests_dialog.foo_action"
    - slot: TO
      action: 
        text: "Where do you want to travel?"
        replies: generator_fn

  - name: 'show'
    action:
      text: "Some text message"
      replies: [ 'Yes', 'No' ]
      next: "help.root"

help:
  states:

  - name: 'root'
    action: !!python/name:botshot.core.tests_dialog.foo_action

  - name: 'image'
    action:
      image_url: 'https://placehold.it/300x300'
      next: 'default.root'

generative:
  states:
  - name: 'qa'
    action:
      type: 'QA'
      context: 'generic_questions.txt'

  - name: 'free'
    action:
      type: 'free_input'
      message: 'Type your feedback please'
      callback: example.some_function

  - name: 'seq2seq'
    action:
      type: 'seq2seq'
      from: 'my_nn_weights_1'
"""


FILTERING_EXAMPLE_YAML = """
greeting:
    states:
    - name: morning
      action:
        text: "Good morning!"
      on:
        datetime: TODO bind predicates from python 
"""


class NewStatesTestCase(unittest.TestCase):
    def test_load_from_yaml(self):
        from botshot.core.flow import load_flows_from_definitions
        import yaml
        definitions = yaml.load(TEST_YAML)
        flows = load_flows_from_definitions(definitions)
        self.assertIsNotNone(flows)
        self.assertEqual(len(flows), 3)
        ret = flows['help']['root'].action()
        self.assertEqual(ret, 1)
        ret = flows['default']['root'].action()
        self.assertEqual(ret, 1)


class ContextTestCase(unittest.TestCase):
    pass


class DialogManagerTestCase(unittest.TestCase):
    pass


def foo_action():
    return 1


if __name__ == '__main__':
    unittest.main()

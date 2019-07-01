from botshot.core.parsing import EntityExtractor


class GolemExtractor(EntityExtractor):

    def __init__(self):
        super().__init__()
        self.nlu = None

    def extract_entities(self, text: str, max_retries=1, **kwargs):
        if not self.nlu:
            from botshot.nlu.predict import GolemNLU
            self.nlu = GolemNLU()
            global GOLEM_NLU
            GOLEM_NLU = self.nlu

        # TODO use a separate thread (pool) to remove TF memory overhead
        return self.nlu.parse(text)


GOLEM_NLU = None

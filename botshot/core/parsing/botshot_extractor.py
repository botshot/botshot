from botshot.core.parsing.entity_extractor import EntityExtractor


class BotshotExtractor(EntityExtractor):

    def __init__(self):
        super().__init__()
        self.nlu = None

    def extract_entities(self, text: str, max_retries=1):
        if not self.nlu:
            from botshot.nlu.predict import BotshotNLU
            self.nlu = BotshotNLU.load()
            global BOTSHOT_NLU
            BOTSHOT_NLU = self.nlu

        # TODO use a separate thread (pool) to remove TF memory overhead
        return self.nlu.parse(text)


BOTSHOT_NLU = None

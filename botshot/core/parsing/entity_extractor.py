from abc import ABC, abstractmethod


class EntityExtractor(ABC):
    """
    Abstract class for entity extractors.
    Responsible for processing text and extracting entities such as names, dates, places etc.
    """

    def __init__(self):
        pass

    @abstractmethod
    def extract_entities(self, text: str, max_retries=5):
        """
        Extracts entities from text (a message from user).
        :param text:        a string.
        :param max_retries: how many times to retry on error.
        :return: A dict of extracted entities.
                 For example:
                 {
                    "place": [
                        {"value": "Prague"},
                        {"value": "New York", "metadata": {}}
                    ],
                    "name": [{"value": "Golem"}],
                    ...
                 }
        """
        return dict()

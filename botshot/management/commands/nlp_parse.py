from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Parses a sentence using NLP module'

    def add_arguments(self, parser):
        parser.add_argument('text', nargs=1, type=str)

    def handle(self, *args, **options):
        from botshot.nlu.predict import GolemNLU
        from pprint import pprint
        text = options['text'][0]
        if isinstance(text, str):
            nlu = GolemNLU()
            entities = nlu.parse(text)
            pprint(entities)
        else:
            raise ValueError('Text must be a string')

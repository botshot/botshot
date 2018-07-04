from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Trains the NLU for text entity extraction'

    def add_arguments(self, parser):
        parser.add_argument('entity', nargs='+', type=str)

    def handle(self, *args, **options):
        from botshot.nlu import train
        if options.get('entity'):
            if options['entity'][0] == 'all':
                train.train_all()
            train.train_all(options['entity'])
        else:
            raise Exception()

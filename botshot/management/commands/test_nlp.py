from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Runs NLU tests'

    def add_arguments(self, parser):
        parser.add_argument('text', nargs='+', type=str)

    def handle(self, *args, **options):
        # from botshot.nlp import train
        # train.test_all()
        raise NotImplementedError("TO DO")

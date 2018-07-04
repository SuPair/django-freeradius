import sys
from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.management import BaseCommand, CommandError

from django_freeradius.models import RadiusBatch
from django_freeradius.settings import BATCH_DEFAULT_PASSWORD_LENGTH


class Command(BaseCommand):
    help = "Add a batch of users from a file"

    def add_arguments(self, parser):
        parser.add_argument('--name',
                            action='store',
                            help='Name of the event of batch addition')
        parser.add_argument('--file',
                            action='store',
                            help='Will import users from the file')
        parser.add_argument('--expiration',
                            action='store',
                            default=None,
                            help='Will deactivate users after this date')
        parser.add_argument('--password-length',
                            action='store',
                            default=BATCH_DEFAULT_PASSWORD_LENGTH,
                            type=int)

    def handle(self, *args, **options):
        try:
            csvfile = open(options['file'], 'rt')
        except IOError:
            raise CommandError('File does not exist')
        expiration_date = options['expiration']
        if expiration_date:
            expiration_date = datetime.strptime(expiration_date, '%d-%m-%Y')
        batch = RadiusBatch(name=options['name'], strategy='csv', expiration_date=expiration_date)
        batch.save()
        batch.csvfile.save(csvfile.name.split('/')[-1], File(csvfile))
        csvfile.seek(0)
        try:
            batch.csvfile_upload(csvfile, options['password_length'])
        except ValidationError:
            batch.delete()
            self.stdout.write('Error in uploading users from the file')
            sys.exit(1)
        self.stdout.write('Added a batch of users from a csv file')
        csvfile.close()

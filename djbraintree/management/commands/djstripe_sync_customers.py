# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from ...settings import get_payer_model
from ...sync import sync_entity


class Command(BaseCommand):

    help = "Sync subscriber data with Braintree"

    def handle(self, *args, **options):
        qs = get_payer_model().objects.filter(customer__isnull=True)
        count = 0
        total = qs.count()
        for entity in qs:
            count += 1
            perc = int(round(100 * (float(count) / float(total))))
            print(
                "[{0}/{1} {2}%] Syncing {3} [{4}]".format(
                    count, total, perc, entity.email, entity.pk
                )
            )
            sync_entity(entity)
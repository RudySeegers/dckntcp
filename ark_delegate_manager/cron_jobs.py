from django_cron import CronJobBase, Schedule
from ark_delegate_manager.models import VotePool
import arkdbtools.dbtools as ark_node
import arkdbtools.config as info
import logging
import ark_delegate_manager.constants as constants
logger = logging.getLogger(__name__)
import datetime
from django.conf import settings
from . import config
from . import payout_functions
import console.models
from arky import api
import arkdbtools.config as arkinfo
import arkdbtools.dbtools as dbtools
from . import models


class UpdateVotePool(CronJobBase):
    RUN_EVERY_MINS = 20
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.update_vote_pool'

    def do(self):
        logger.info('starting share calculation')
        ark_node.set_connection(
            host=config.CONNECTION['HOST'],
            database=config.CONNECTION['DATABASE'],
            user=config.CONNECTION['USER'],
            password=config.CONNECTION['PASSWORD']
        )

        ark_node.set_delegate(
            address=config.DELEGATE['ADDRESS'],
            pubkey=config.DELEGATE['PUBKEY'],
        )

        if not ark_node.Node.check_node(51):
            logger.fatal('Node is more than 51 blocks behind')
            raise ark_node.NodeDbError('Node is more than 51 blocks behind')

        payouts, timestamp = ark_node.Delegate.trueshare()

        for address in payouts:
            VotePool.objects.get_or_create(ark_address=address)
        for voter in VotePool.objects.all():
            voter.payout_amount = payouts[voter]['share']


class RunPayments(CronJobBase):
    RUN_EVERY_MINS = 2
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.update_vote_pool'

    def do(self):
        logger.info('starting payment run')

        if not ark_node.Node.check_node(51):
            logger.fatal('Node is more than 51 blocks behind')
            raise ark_node.NodeDbError('Node is more than 51 blocks behind')

        payouts, timestamp = ark_node.Delegate.trueshare()
        logger.info('starting payment run at arktimestamp: {}'.format(timestamp))
        payout_functions.paymentrun(
            payout_dict=payouts,
            current_timestamp=timestamp
        )


class VerifyReceivingArkAddresses(CronJobBase):
    RUN_EVERY_MINS = 10
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.verify_receiving_ark_addresses'

    def do(self):
        logger.info('starting verification update round. CODE: {}'.format('ark_delegate_manager.verify_receiving_ark_addresses'))
        payout_functions.verify_address_run()


class UpdateDutchDelegateStatus(CronJobBase):
    RUN_EVERY_MINS = 10
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.update_dutch_delegate_status'

    def do(self):
        payout_functions.update_arknode()

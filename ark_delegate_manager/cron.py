from django_cron import CronJobBase, Schedule
from ark_delegate_manager.models import VotePool, ArkDelegates
import arkdbtools.dbtools as ark_node
import arkdbtools.utils as utils
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
import ark_delegate_manager


class UpdateVotePool(CronJobBase):
    RUN_EVERY_MINS = 30
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.update_vote_pool'
    logger.info('updating votepool')

    def do(self):
        try:
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

            if not ark_node.Node.check_node(51) and settings.DEBUG == False:
                logger.fatal('Node is more than 51 blocks behind')
                return
            try:
                payouts, timestamp = ark_node.Delegate.trueshare()
            except Exception:
                logger.exception('failed to calculate payouts')
                return
            for address in payouts:
                voter, created = VotePool.objects.update_or_create(
                    ark_address=address)
                voter.payout_amount = payouts[address]['share']
                voter.save()
        except Exception:
            logger.exception('error in UpdateVotePool')


class RunPayments(CronJobBase):
    RUN_EVERY_MINS = 120
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.update_vote_pool'

    def do(self):
        try:
            logger.critical('starting payment run')

            if not ark_node.Node.check_node(51) and settings.DEBUG == False:
                logger.fatal('Node is more than 51 blocks behind')
                return

            payouts, timestamp = ark_node.Delegate.trueshare()
            logger.info('starting payment run at arktimestamp: {}'.format(timestamp))
            payout_functions.paymentrun(
                payout_dict=payouts,
                current_timestamp=timestamp
            )
        except Exception:
            logger.exception('error in RunPayments')


class VerifyReceivingArkAddresses(CronJobBase):
    RUN_EVERY_MINS = 10
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.verify_receiving_ark_addresses'

    def do(self):
        logger.info('starting verification update round. CODE: {}'.format('ark_delegate_manager.verify_receiving_ark_addresses'))

        if not ark_node.Node.check_node(51) and settings.DEBUG == False:
            logger.fatal('Node is more than 51 blocks behind')
            return
        try:
            payout_functions.verify_address_run()
        except Exception:
            logger.exception('Error during VerifyReceivingArkAddresses')


class UpdateDutchDelegateStatus(CronJobBase):
    RUN_EVERY_MINS = 10
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.update_dutch_delegate_status'

    def do(self):
        try:
            payout_functions.update_arknode()
        except Exception:
            logger.exception('Error during UpdateDutchDelegateStatus')


class UpdateDelegates(CronJobBase):
    RUN_EVERY_MINS = 30
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.update_delegates'

    def do(self):
        try:
            api.use('ark')
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
            all_delegates = utils.api_call(api.Delegate.getDelegates)['delegates']
            for delegate in all_delegates:
                delegate_obj = ark_delegate_manager.models.ArkDelegates.objects.get_or_create(pubkey=delegate['publicKey'])[0]
                delegate_obj.username = delegate['username']
                delegate_obj.address = delegate['address']
                delegate_obj.ark_votes = delegate['vote']
                delegate_obj.producedblocks = delegate['producedblocks']
                delegate_obj.missedblocks = delegate['missedblocks']
                delegate_obj.productivity = delegate['productivity']
                delegate_obj.rank = delegate['rate']
                delegate_obj.voters = len(ark_node.Delegate.voters(delegate['address'])) + 1
                delegate_obj.save()
        except Exception:
            logger.exception('Error during UpdateDelegates')

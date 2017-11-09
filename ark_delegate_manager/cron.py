from django_cron import CronJobBase, Schedule
from ark_delegate_manager.models import VotePool
import arkdbtools.dbtools as ark_node
import arkdbtools.config as info
import logging
import ark_delegate_manager.constants as constants
import datetime
from django.conf import settings
from . import config
from . import payout_functions
import console.models
from arky import api
import arkdbtools.config as arkinfo
import arkdbtools.dbtools as dbtools
from . import models
import kronos
from django.conf import settings
logger = logging.getLogger(__name__)


@kronos.register('0 0 * * *')
def update_share_calculations():
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

    if not ark_node.Node.check_node(51) and settings.DEBUG is False:
        logger.fatal('Node is more than 51 blocks behind')
        return
    payouts, timestamp = ark_node.Delegate.trueshare()

    for address in payouts:
        VotePool.objects.get_or_create(ark_address=address)
    for voter in VotePool.objects.all():
        voter.payout_amount = payouts[voter]['share']


@kronos.register('0 0 * * *')
def paymentrun_ark():
    logger.critical('starting payment run')

    if not ark_node.Node.check_node(51) and settings.DEBUG is False:
        logger.fatal('Node is more than 51 blocks behind')
        return

    payouts, timestamp = ark_node.Delegate.trueshare()
    logger.info('starting payment run at arktimestamp: {}'.format(timestamp))
    payout_functions.paymentrun(
        payout_dict=payouts,
        current_timestamp=timestamp
    )


@kronos.register('0 0 * * *')
def verify_address_run():
    logger.info('starting verification update round. CODE: {}'.format('ark_delegate_manager.verify_receiving_ark_addresses'))

    if not ark_node.Node.check_node(51) and settings.DEBUG is False:
        logger.fatal('Node is more than 51 blocks behind')
        return

    payout_functions.verify_address_run()


@kronos.register('0 0 * * *')
def update_arknode_stats():
    logger.info('updating arkdelegate stats')
    payout_functions.update_arknode()

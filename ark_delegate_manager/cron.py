from django_cron import CronJobBase, Schedule
from ark_delegate_manager.models import VotePool, ArkDelegates, Node
import arkdbtools.dbtools as ark_node
import arkdbtools.utils as utils
import arkdbtools.config as info
import logging
import ark_delegate_manager.constants as constants
from django.conf import settings
from . import config
from . import custom_functions
import ark_delegate_manager
from arkdbtools.config import ARK
from arky import api
from ark_delegate_manager.custom_functions import send_tx
from decouple import config as conf
import ark_delegate_manager.models
import time

logger = logging.getLogger(__name__)


class UpdateVotePool(CronJobBase):
    RUN_EVERY_MINS = 15
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.update_vote_pool'

    def do(self):
        '''
        add voters to our record of all voters and calculate their balances
        '''
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

                if voter.status == "Non-Dutchdelegate Voter":
                    continue

                if payouts[address]['vote_timestamp'] < constants.CUT_OFF_EARLY_ADOPTER:
                    voter.status = "Early adopter"
                    voter.share = 0.96
                else:
                    voter.status = "Regular Voter"
                    voter.share = 0.95
                
                voter.payout_amount = (payouts[address]['share'] * voter.share)
                voter.save()

        except Exception:
            logger.exception('error in UpdateVotePool')


class RunPayments(CronJobBase):

    RUN_EVERY_MINS = 360

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.run_payments'

    def do(self):

        '''
        calculate and run weekly payouts
        '''
        try:
            custom_functions.set_lock(name='RunPayments')
        except Exception:
            raise

        try:
            if settings.DEBUG:
                logger.info('faking payment run')
                time.sleep(120)
            elif not settings.DEBUG:
                custom_functions.payment_run()
        except Exception:
            logger.exception('failed payment run')
            raise

        # this sleep ensures the ark-node has time to receive the new transactions
        if not settings.DEBUG:
            time.sleep(constants.HOUR/2)
        try:
            custom_functions.release_lock(name='RunPayments')
        except Exception:
            logger.exception('failed to clear payment_run_lock')
            raise


class VerifyReceivingArkAddresses(CronJobBase):
    RUN_EVERY_MINS = 10
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.verify_receiving_ark_addresses'

    def do(self):
        '''
        check blockchain for wallet verification tokens
        '''
        logger.info('starting verification update round. CODE: {}'.format('ark_delegate_manager.verify_receiving_ark_addresses'))

        if not ark_node.Node.check_node(51) and settings.DEBUG == False:
            logger.fatal('Node is more than 51 blocks behind')
            return
        try:
            custom_functions.verify_address_run()
        except Exception:
            logger.exception('Error during VerifyReceivingArkAddresses')


class UpdateDutchDelegateStatus(CronJobBase):
    RUN_EVERY_MINS = 10
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.update_dutch_delegate_status'

    def do(self):
        '''
        update the ark-node statistics
        '''
        try:
            custom_functions.update_arknode()
        except Exception:
            logger.exception('Error during UpdateDutchDelegateStatus')


class UpdateDelegates(CronJobBase):
    RUN_EVERY_MINS = 30
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.update_delegates'

    def do(self):
        '''
        update delegate statistics and save in DB
        '''
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


class GetBlockchainHeight(CronJobBase):
    RUN_EVERY_MINS = 5
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.get_blockchain_height'

    def do(self):
        '''
        update the currenct blockchain height and save it in DB
        '''
        try:
            ark_node.set_connection(
                host=config.CONNECTION['HOST'],
                database=config.CONNECTION['DATABASE'],
                user=config.CONNECTION['USER'],
                password=config.CONNECTION['PASSWORD']
            )



            api.use('ark')
            blockchain_height = ark_node.Blockchain.height()
            node = Node.objects.get_or_create(id='main')[0]
            node.blockchain_height = blockchain_height
            node.save()
        except Exception:
            logger.exception('failed to update blockchain height')


class PayRewardsWallet(CronJobBase):
    RUN_EVERY_MINS = constants.WEEK/constants.MINUTE
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.pay_rewards_wallet'

    def do(self):
        '''
        payout the delegate reward after saving the payouts for a certain time
        '''

        try:
            delegate = ark_delegate_manager.models.DutchDelegateStatus.objects.get(id='main')
            reward = delegate.reward
            res = send_tx(conf('REWARDWALLET'), reward)
            if not res:
                logger.critical('failed to send rewardpayment to rewardswallet')
            else:
                delegate.reward = 0
                delegate.save()
        except Exception:
            logger.exception('failed to transmit the delegate reward: {}'.format(reward/ARK))


# this cronjob updates historic delegates
class UpdateDelegatesBlockchain(CronJobBase):
    RUN_EVERY_MINS = 10000
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.update_delegate_blockchain'

    def do(self):
        """
        update the delegate database with historic delegates. This also obtains data on delegates below the top 51.
        """
        try:

            ark_node.set_connection(
                host=config.CONNECTION['HOST'],
                database=config.CONNECTION['DATABASE'],
                user=config.CONNECTION['USER'],
                password=config.CONNECTION['PASSWORD']
            )

            all_delegates = ark_node.Delegate.delegates()

            for i in all_delegates:
                delegate, created = ark_delegate_manager.models.ArkDelegates.objects.get_or_create(pubkey=i.pubkey)
                if created:
                    delegate.address = i.address
                    delegate.username = i.username
                    delegate.save()
        except Exception:
            logger.exception('failure in UpdateDelegatesBlockchain')

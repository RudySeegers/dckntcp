import arkdbtools.dbtools as ark_node
import arkdbtools.config as info
import logging
import ark_delegate_manager.constants as constants
import ark_delegate_manager.models
import arky.core, arky.api
from django.conf import settings
from . import config
import console.models
import hashlib
import arkdbtools.utils as utils
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction



logger = logging.getLogger(__name__)


class ConcurrencyError(Exception):
    pass


class LockError(Exception):
    pass


def send_tx(address, amount, vendor_field=''):

    # if we are in testmode, don't actually send the transaction, but log the result:
    if settings.DEBUG:
        logger.info('TESTTRANSACTON: ADDRESS  {0}, AMOUNT: {1}'.format(address, amount / info.ARK))
        return True

    tx = arky.core.Transaction(
        amount=amount,
        recipientId=address,
        vendorField=vendor_field
    )
    tx.sign(config.DELEGATE['SECRET'])
    tx.serialize()
    arky.api.use('ark')
    result = arky.api.broadcast(tx)
    if result['success']:
        logger.info('succesfull transacton for {0}, '
                    'for amount: {1}. RESPONSE: {2}'.format(address, amount/info.ARK, result))

        return True
    # if after 5 attempts we still failed:
    if not result['success']:
        logger.warning('failed transaction for {0}, for amount: {1}. RESPONSE: {2}'.format(address,
                                                                                           amount/info.ARK,
                                                                                           result))
        return False


def verify_address_run():
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

    cursor = ark_node.DbCursor()

    qry = cursor.execute_and_fetchall("""
            SELECT transactions"vendorField", transactions."senderId"
            FROM transactions
            WHERE transactions."recipientId" = '{0}'
            ORDER BY transactions."timestamp" ASC;
            """.format(config.DELEGATE['ADDRESS']))

    for i in qry:
        try:
            vendor_field = i[0]
            sender_id = i[1]
            user = console.models.UserProfile.objects.get(main_ark_wallet=sender_id)
            rawtoken = settings.VERIFICATION_KEY + str(user) + 'ark'
            token = hashlib.sha256(rawtoken.encode()).hexdigest()
            if token in vendor_field:
                user.receiving_ark_address_verified = True
            if 'CANCEL VERIFICATION' in vendor_field:
                user.receiving_ark_address_verified = False
        except Exception:
            pass


def update_arknode():
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

        logger.info('starting updaterun dutchdelegate info')
        for i in range(5):
            try:
                arky.api.use('ark')
                dutchdelegatestatus = utils.api_call(arky.api.Delegate.getDelegate, 'dutchdelegate')
                if not dutchdelegatestatus['success']:
                    logger.fatal('unable to update the status of dutchdelegate node after 5 tries: response: {}'.format(
                        dutchdelegatestatus))
                    return

                data = ark_delegate_manager.models.DutchDelegateStatus.objects.get_or_create(id='main')[0]
                data.rank = int(dutchdelegatestatus['delegate']['rate'])
                data.ark_votes = int(dutchdelegatestatus['delegate']['vote']) / info.ARK
                data.voters = len(ark_node.Delegate.voters())
                data.productivity = float(dutchdelegatestatus['delegate']['productivity'])
                data.save()
            except Exception:
                logger.exception('error in update_arknode')


@transaction.atomic
def set_lock_payment_run():
    lock = ark_delegate_manager.models.PaymentLock.objects.select_for_update().get(id='main')
    if lock.lock:
        logger.fatal('paymentrun was started with PaymentLock on.')
        raise ConcurrencyError('paymentrun was started with PaymentLock on.')
    else:
        lock.lock = True
        lock.save()


@transaction.atomic
def release_lock_payment_run():
    lock = ark_delegate_manager.models.PaymentLock.objects.select_for_update().get(id='main')
    lock.lock = False
    lock.save()


def payment_run():
    logger.critical('starting payment run')
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

    # if we are in test mode we don't care about our node status
    if not ark_node.Node.check_node(51) and not settings.DEBUG:
        logger.fatal('Node is more than 51 blocks behind')
        return

    payouts, current_timestamp = ark_node.Delegate.trueshare()

    for voter in payouts:
        send_destination = ark_delegate_manager.models.PayoutTable.objects.get_or_create(address=voter)
        send_destination.amount = voter['share']
        send_destination.vote_timestamp = voter['vote_timestamp']
        send_destination.status = voter['status']
        send_destination.last_payout_blockchain_side = voter['last_payout']
        send_destination.save()

    # and now on to actually sending the payouts
    failed_transactions = 0
    failed_amount = 0
    succesful_transactions = 0
    succesful_amount = 0
    vendorfield = ark_delegate_manager.models.Setting.objects.get(id='main').vendorfield

    payout_exceptions = ark_delegate_manager.models.EarlyAdopterAddressException.objects.all().values_list(
        'new_ark_address', flat=True)

    blacklist = ark_delegate_manager.models.BlacklistedAddress.objects.all().values_list(
        'ark_address', flat=True)

    for send_destination in ark_delegate_manager.models.PayoutTable.objects.all():
        address = send_destination.address
        pure_amount = send_destination.amount
        vote_timestamp = send_destination.vote_timestamp
        status = send_destination.status
        last_payout = send_destination.last_payout_blockchain_side
        last_payout_server_side = send_destination.last_payout_server_side

        if current_timestamp < last_payout_server_side:
            logger.fatal('double payment run occuring')
            raise ConcurrencyError('double payment run occuring, lock needs to be manually removed')

        if current_timestamp - last_payout_server_side < 15 * constants.HOUR:
            logger.fatal('Time between payouts less than 15 hours according to server.')
            raise ConcurrencyError('double payment run occuring, lock needs to be manually removed')

        if address in blacklist:
            continue

        share_percentage = 0.95
        frequency = 2
        delegate_share = 0

        try:
            user_settings = console.models.UserProfile.objects.get(main_ark_wallet=address)
            frequency = user_settings.payout_frequency
        except ObjectDoesNotExist:
            pass

        if vote_timestamp < constants.CUT_OFF_EARLY_ADOPTER or address in payout_exceptions:
            share_percentage = 0.96

        amount = pure_amount * share_percentage
        if status:
            if frequency == 1 and last_payout < current_timestamp - (constants.DAY - 3 * constants.HOUR):
                if amount > constants.MIN_AMOUNT_DAILY:
                    amount -= info.TX_FEE
                    res = send_tx(address=send_destination, amount=amount, vendor_field=vendorfield)
                    if res:
                        delegate_share = pure_amount - amount
                        succesful_transactions += 1
                        succesful_amount += amount
                        logger.info('sent {0} to {1}  res: {2}'.format(amount, send_destination, res))
                        send_destination.last_payout_server_side = last_payout
                        send_destination.save()
                    else:
                        failed_transactions += 1
                        failed_amount += amount

            if frequency == 2 and last_payout < current_timestamp - (constants.WEEK - 5 * constants.HOUR):
                if amount > constants.MIN_AMOUNT_WEEKY:
                    res = send_tx(address=send_destination, amount=amount, vendor_field=vendorfield)
                    if res:
                        delegate_share = pure_amount - amount
                        succesful_transactions += 1
                        succesful_amount += amount
                        logger.info('sent {0} to {1}  res: {2}'.format(amount, send_destination, res))
                        send_destination.last_payout_server_side = last_payout
                        send_destination.save()
                    else:
                        failed_transactions += 1
                        failed_amount += amount

            if frequency == 3 and last_payout < (current_timestamp - constants.MONTH - 5 * constants.HOUR):
                if amount > constants.MIN_AMOUNT_MONTHLY:
                    res = send_tx(address=send_destination, amount=amount, vendor_field=vendorfield)
                    if res:
                        delegate_share = pure_amount - amount
                        succesful_transactions += 1
                        succesful_amount += amount
                        logger.info('sent {0} to {1}  res: {2}'.format(amount, send_destination, res))
                        send_destination.last_payout_server_side = last_payout
                        send_destination.save()
                    else:
                        failed_transactions += 1
                        failed_amount += amount

            dutchdelegate = ark_delegate_manager.models.DutchDelegateStatus.objects.get_or_create(id='main')
            dutchdelegate.reward += delegate_share
            dutchdelegate.save()

    if failed_transactions:
        logger.critical('sent {0} transactions, failed {1} transactions'.format(succesful_transactions,
                                                                                failed_transactions))
        logger.critical('amout successful: {0}, failed amount: {1}'.format(succesful_amount / info.ARK,
                                                                           failed_amount / info.ARK))
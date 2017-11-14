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
logger = logging.getLogger(__name__)


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


def paymentrun(payout_dict, current_timestamp):
    failed_transactions = 0
    failed_amount = 0
    succesful_transactions = 0
    succesful_amount = 0
    for voter in payout_dict:

        send_destination = voter
        share_percentage = 0.95
        frequency = 2
        verified = False
        delegate_share = 0
        try:
            user_settings = console.models.UserProfile.objects.get(main_ark_wallet=voter)
            frequency = user_settings.payout_frequency
            # receiving_address = user_settings.receiving_ark_address
            # verified = user_settings.receiving_ark_address_verified
            # send_to_second = user_settings.ark_send_to_second_address

            #send_to_second is not a bool, because the widget for an integerfield is much prettier
            # if verified and send_to_second == 1:
            #     send_destination = receiving_address
        except Exception:
            pass
        if payout_dict[voter]['vote_timestamp'] < constants.CUT_OFF_EARLY_ADOPTER or voter in constants.PAYOUT_EXCEPTIONS:
            share_percentage = 0.96

        amount = payout_dict[voter]['share'] * share_percentage

        if frequency == 1 and payout_dict[voter]['last_payout'] < current_timestamp - (constants.DAY - 7 * constants.HOUR):
            if amount > constants.MIN_AMOUNT_DAILY:
                # admin_res = send_tx(address=voter, amount=1,
                #                     vendor_field='|DD-admin| sent payout to: '.format(send_destination))
                res = send_tx(address=send_destination, amount=amount)
                if res:
                    delegate_share = payout_dict[voter]['share'] - amount
                    succesful_transactions += 1
                    succesful_amount += amount
                    logger.info('sent {0} to {1}  res: {2}'.format(amount, send_destination, res))
                else:
                    failed_transactions += 1
                    failed_amount += amount
                # if res and verified:
                #     if not admin_res:
                #         logger.fatal('failed to send administrative token to {}'.format(voter))
        if frequency == 2 and payout_dict[voter]['last_payout'] < current_timestamp - (constants.WEEK - 4 * constants.HOUR):
            if amount > constants.MIN_AMOUNT_WEEKY:
                amount += info.TX_FEE

                # admin_res = send_tx(address=voter, amount=1,
                #                     vendor_field='|DD-admin| sent payout to: '.format(send_destination))
                res = send_tx(address=send_destination, amount=amount)
                if res:
                    delegate_share = payout_dict[voter]['share'] - amount
                    succesful_transactions += 1
                    succesful_amount += amount
                    logger.info('sent {0} to {1}  res: {2}'.format(amount, send_destination, res))
                else:
                    failed_transactions += 1
                    failed_amount += amount

                # if res and verified:
                #     if not admin_res:
                #         logger.fatal('failed to send administrative token to {}'.format(voter))
        if frequency == 3 and payout_dict[voter]['last_payout'] < current_timestamp - constants.MONTH:
            if amount > constants.MIN_AMOUNT_MONTHLY:
                amount += info.TX_FEE
                # admin_res = send_tx(address=voter, amount=1,
                #                     vendor_field='|DD-admin| sent payout to: '.format(send_destination))
                res = send_tx(address=send_destination, amount=amount)
                if res:
                    delegate_share = payout_dict[voter]['share'] - amount
                    succesful_transactions += 1
                    succesful_amount += amount
                    logger.info('sent {0} to {1}  res: {2}'.format(amount, send_destination, res))
                else:

                    failed_transactions += 1
                    failed_amount += amount
        try:
            dutchdelegate = ark_delegate_manager.models.DutchDelegateStatus.objects.get(id='main')
            dutchdelegate.reward += delegate_share
            dutchdelegate.save()
        except Exception:
            pass
    if failed_transactions:
        logger.critical('sent {0} transactions, failed {1} transactions'.format(succesful_transactions, failed_transactions))
        logger.critical('amout successful: {0}, failed amount: {1}'.format(succesful_amount/info.ARK, failed_amount/info.ARK))


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




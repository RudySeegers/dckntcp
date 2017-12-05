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
import datetime
from urllib3.exceptions import ReadTimeoutError
from django.template.loader import render_to_string, get_template


logger = logging.getLogger(__name__)


class ConcurrencyError(Exception):
    pass


class LockError(Exception):
    pass
from django.contrib.auth.models import User
from django.core.mail import send_mail as core_send_mail
from django.core.mail import EmailMultiAlternatives
import threading


class EmailThread(threading.Thread):
    def __init__(self, subject, body, from_email, recipient_list, fail_silently, html):
        self.subject = subject
        self.body = body
        self.recipient_list = recipient_list
        self.from_email = from_email
        self.fail_silently = fail_silently
        self.html = html
        threading.Thread.__init__(self)

    def run (self):
        msg = EmailMultiAlternatives(self.subject, self.body, self.from_email, self.recipient_list)
        if self.html:
            msg.attach_alternative(self.html, "text/html")
        msg.send(self.fail_silently)


def send_mail(subject, body, from_email, recipient_list, fail_silently=False, html=None, *args, **kwargs):
    EmailThread(subject, body, from_email, recipient_list, fail_silently, html).start()


def send_tx(address, amount, vendor_field=''):

    # if we are in testmode, don't actually send the transaction, but log the result:
    if settings.DEBUG:
        logger.info('TESTTRANSACTON: ADDRESS  {0}, AMOUNT: {1}'.format(address, amount / info.ARK))
        return True
    try:
        tx = arky.core.Transaction(
            amount=amount,
            recipientId=address,
            vendorField=vendor_field
        )
        tx.sign(config.DELEGATE['SECRET'])
        tx.serialize()
        arky.api.use('ark')
        result = arky.api.broadcast(tx)
    except ReadTimeoutError:
        # we'll make a single retry in case of a ReadTimeOutError. We are sending the exact same TX hash to make
        # sure no double payouts occur
        arky.api.use('ark')
        result = arky.api.broadcast(tx)

    if result['success']:
        logger.info('succesfull transacton for {0}, '
                    'for amount: {1}. RESPONSE: {2}'.format(address, amount/info.ARK, result))

        return True
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
def set_lock(name):
    try:
        lock = ark_delegate_manager.models.CronLock.objects.select_for_update().filter(job_name=name, lock=False).update(lock=True)
        if not lock:
            logger.fatal('{} lock was True while run was initiated.'.format(name))
            raise ConcurrencyError
    except ObjectDoesNotExist:
        logger.fatal('Cannot find lock, make sure to load fixtures')
        raise


@transaction.atomic
def release_lock(name):
    lock = ark_delegate_manager.models.CronLock.objects.select_for_update().filter(job_name=name, lock=True).update(lock=False)
    if not lock:
        logger.fatal('{} lock was False while run was ended.'.format(name))
        raise ConcurrencyError


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
        send_destination = ark_delegate_manager.models.PayoutTable.objects.get_or_create(address=voter)[0]
        send_destination.amount = payouts[voter]['share']
        send_destination.vote_timestamp = payouts[voter]['vote_timestamp']
        send_destination.status = payouts[voter]['status']
        send_destination.last_payout_blockchain_side = payouts[voter]['last_payout']
        send_destination.save()

    # and now on to actually sending the payouts
    failed_transactions = 0
    failed_amount = 0
    succesful_transactions = 0
    succesful_amount = 0
    vendorfield = ark_delegate_manager.models.Setting.objects.get(id='main').vendorfield
    weekday = datetime.datetime.today().weekday()
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

        #preferred day of 8 translated to no preference
        preferred_day = 8
        correctday = True
        if address in blacklist:
            continue

        if current_timestamp < last_payout_server_side:
            logger.fatal('double payment run occuring')
            raise ConcurrencyError('double payment run occuring, lock needs to be manually removed')

        if current_timestamp - last_payout_server_side < 15 * constants.HOUR:
            logger.fatal('Time between payouts less than 15 hours according to server.')
            raise ConcurrencyError('double payment run occuring, lock needs to be manually removed')

        share_percentage = 0.95
        frequency = 2
        delegate_share = 0
        send_email = 1
        try:
            user_settings = console.models.UserProfile.objects.get(main_ark_wallet=address)
            frequency = user_settings.payout_frequency
            preferred_day = int(user_settings.preferred_day)
            send_email = user_settings.send_email_about_payout
        except ObjectDoesNotExist:
            pass

        if vote_timestamp < constants.CUT_OFF_EARLY_ADOPTER or address in payout_exceptions:
            share_percentage = 0.96

        amount = pure_amount * share_percentage
        if preferred_day == 8:
            correctday = True
        elif preferred_day != weekday:
            correctday = False

        if status and correctday:
            if frequency == 1 and last_payout < current_timestamp - (constants.DAY - 3 * constants.HOUR):
                if amount > constants.MIN_AMOUNT_DAILY:
                    amount -= info.TX_FEE
                    res = send_tx(address=send_destination.address, amount=amount, vendor_field=vendorfield)
                    if res:
                        delegate_share = pure_amount - (amount + info.TX_FEE)
                        succesful_transactions += 1
                        succesful_amount += amount
                        logger.info('sent {0} to {1}  res: {2}'.format(amount, send_destination, res))
                        send_destination.last_payout_server_side = last_payout
                        send_destination.save()
                        user_settings.send_email_about_payout = True
                        user_settings.save()
                    else:
                        failed_transactions += 1
                        failed_amount += amount

            if frequency == 2 and last_payout < current_timestamp - (constants.WEEK - 5 * constants.HOUR):
                if amount > constants.MIN_AMOUNT_WEEKY:
                    res = send_tx(address=send_destination.address, amount=amount, vendor_field=vendorfield)
                    if res:
                        delegate_share = pure_amount - (amount + info.TX_FEE)
                        succesful_transactions += 1
                        succesful_amount += amount
                        logger.info('sent {0} to {1}  res: {2}'.format(amount, send_destination, res))
                        send_destination.last_payout_server_side = last_payout
                        send_destination.save()
                        user_settings.send_email_about_payout = True
                        user_settings.save()
                    else:
                        failed_transactions += 1
                        failed_amount += amount

            if frequency == 3 and last_payout < (current_timestamp - constants.MONTH - 5 * constants.HOUR):
                if amount > constants.MIN_AMOUNT_MONTHLY:
                    amount += 1.5 * info.TX_FEE
                    res = send_tx(address=send_destination.address, amount=amount, vendor_field=vendorfield)
                    if res:
                        delegate_share = pure_amount - amount
                        succesful_transactions += 1
                        succesful_amount += amount
                        send_destination.last_payout_server_side = last_payout
                        send_destination.save()
                        user_settings.send_email_about_payout = True
                        user_settings.save()
                    else:
                        failed_transactions += 1
                        failed_amount += amount

            dutchdelegate = ark_delegate_manager.models.DutchDelegateStatus.objects.get_or_create(id='main')[0]
            dutchdelegate.reward += delegate_share
            dutchdelegate.save()

    if failed_transactions:
        logger.critical('sent {0} transactions, failed {1} transactions'.format(succesful_transactions,
                                                                                failed_transactions))
        logger.critical('amout successful: {0}, failed amount: {1}'.format(succesful_amount / info.ARK,
                                                                           failed_amount / info.ARK))
    return True

@transaction.atomic()
def inform_about_payout_run():
    users = console.models.UserProfile.objects.all()
    news_link = ark_delegate_manager.models.Setting.objects.get(id='main').news_link
    for user in users:
        if user.send_email_about_payout and user.inform_by_email:
            recip = User.objects.get(user=user)
            email_address = recip.email
            name = recip.username
            user.send_email_about_payout = False
            user.save()
            context = {
                'name': name,
                'address': user.main_ark_wallet,
                'news_link': news_link
            }
            html_message = render_to_string('../templates/emails/payout_email.html', context)
            send_mail(
                subject='A new payout has been made.',
                body=html_message,
                html=html_message,
                from_email='dutchdelegate@gmail.com',
                recipient_list=[email_address]
            )

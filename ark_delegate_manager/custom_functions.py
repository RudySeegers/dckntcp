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
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
import threading


logger = logging.getLogger(__name__)


class ConcurrencyError(Exception):
    pass


class LockError(Exception):
    pass


# we are threadingnc emails so we're non-blocking.
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
    try:
        tx = arky.core.Transaction(
            amount=amount,
            recipientId=address,
            vendorField=vendor_field
        )
        tx.sign(config.DELEGATE['SECRET'])
        tx.serialize()
        result = arky.api.sendTx(tx=tx, url_base=settings.ARKNODE_PARAMS['IP'])
    except ReadTimeoutError:
        # we'll make a single retry in case of a ReadTimeOutError. We are sending the exact same TX hash to make
        # sure no double payouts occur
        result = arky.api.sendTx(tx=tx, url_base=settings.ARKNODE_PARAMS['IP'])

    print(result)
    return result


# this function is currently not being used. Later we will implement verified accounts
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


#updating the status of dutchdelegate in /console/
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
            raise ConcurrencyError
    except ObjectDoesNotExist:
        logger.fatal('Cannot find lock, make sure to load fixtures')
        raise


@transaction.atomic
def release_lock(name):
    lock = ark_delegate_manager.models.CronLock.objects.select_for_update().filter(job_name=name, lock=True).update(lock=False)
    if not lock:
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

    arky.api.use(network='ark')

    custom_exceptions = ark_delegate_manager.models.CustomAddressExceptions.objects.all()

    for voter in payouts:
        share = 0.95
        preferred_day = 8
        frequency = 2
        vote_timestamp = payouts[voter]['vote_timestamp']

        # this was part of our Early Adopter bonus, where early voters permanently received a 96% share
        if vote_timestamp < constants.CUT_OFF_EARLY_ADOPTER:
            share = 0.96

        try:
            # we can also designate a custom share
            share = custom_exceptions.get(new_ark_address=voter).share_RANGE_IS_0_TO_1

            # a share if 0 means they are blacklisted, so we continue to the next voter
            if share == 0:
                continue

            user_settings = console.models.UserProfile.objects.get(main_ark_wallet=voter)
            frequency = user_settings.payout_frequency
            preferred_day = int(user_settings.preferred_day)
        except Exception:
            pass

        send_destination = ark_delegate_manager.models.PayoutTable.objects.get_or_create(address=voter)[0]
        send_destination.amount = payouts[voter]['share']
        send_destination.vote_timestamp = vote_timestamp
        send_destination.status = payouts[voter]['status']
        send_destination.last_payout_blockchain_side = payouts[voter]['last_payout']
        send_destination.share = share
        send_destination.preferred_day = preferred_day
        send_destination.frequency = frequency
        send_destination.save()

    # and now on to actually sending the payouts
    failed_transactions = 0
    failed_amount = 0
    succesful_transactions = 0
    succesful_amount = 0
    vendorfield = ark_delegate_manager.models.Setting.objects.get(id='main').vendorfield
    weekday = datetime.datetime.today().weekday()

    # we now iterate over the previously generated table.
    for send_destination in ark_delegate_manager.models.PayoutTable.objects.all():
        address = send_destination.address
        share_ratio = send_destination.share
        pure_amount = send_destination.amount
        frequency = send_destination.frequency
        status = send_destination.status
        last_payout = send_destination.last_payout_blockchain_side
        last_payout_server_side = send_destination.last_payout_server_side

        #preferred day of 8 translated to no preference
        preferred_day = 8
        correctday = True

        if current_timestamp < last_payout_server_side:
            logger.fatal('double payment run occuring')
            raise ConcurrencyError('double payment run occuring, lock needs to be manually removed')

        if current_timestamp - last_payout_server_side < 15 * constants.HOUR:
            logger.fatal('Time between payouts less than 15 hours according to server.')
            raise ConcurrencyError('double payment run occuring, lock needs to be manually removed')

        # preferred day of 8
        if preferred_day == 8:
            correctday = True
        elif preferred_day != weekday:
            correctday = False

        delegate_share = 0
        amount = pure_amount * share_ratio

        if status and correctday:
            if frequency == 1 and last_payout < current_timestamp - (constants.DAY - 3 * constants.HOUR):
                if amount > constants.MIN_AMOUNT_DAILY:
                    amount -= info.TX_FEE
                    res = send_tx(address=address, amount=amount, vendor_field=vendorfield)
                    if res['success']:
                        delegate_share = pure_amount - amount
                        succesful_transactions += 1
                        succesful_amount += amount
                        logger.info('sent {0} to {1}  res: {2}'.format(amount, send_destination, res))
                        send_destination.last_payout_server_side = last_payout
                        send_destination.save()
                        user_settings.send_email_about_payout = True
                        user_settings.tx_id = res['transactionIds']
                        user_settings.save()
                    else:
                        failed_transactions += 1
                        failed_amount += amount
                        logger.warning('failed tx {}'.format(res))


            if frequency == 2 and last_payout < current_timestamp - (constants.WEEK - 5 * constants.HOUR):
                if amount > constants.MIN_AMOUNT_WEEKY:
                    res = send_tx(address=address, amount=amount, vendor_field=vendorfield)
                    if res['success']:
                        delegate_share = pure_amount - (amount + info.TX_FEE)
                        succesful_transactions += 1
                        succesful_amount += amount
                        logger.info('sent {0} to {1}  res: {2}'.format(amount, send_destination, res))
                        send_destination.last_payout_server_side = last_payout
                        send_destination.save()
                        user_settings.send_email_about_payout = True
                        user_settings.tx_id = res['transactionIds']
                        user_settings.save()
                    else:
                        failed_transactions += 1
                        failed_amount += amount
                        logger.warning('failed tx {}'.format(res))

            if frequency == 3 and last_payout < (current_timestamp - constants.MONTH - 5 * constants.HOUR):
                if amount > constants.MIN_AMOUNT_MONTHLY:
                    amount += 1.5 * info.TX_FEE
                    res = send_tx(address=address, amount=amount, vendor_field=vendorfield)
                    if res['success']:
                        delegate_share = pure_amount - (amount + info.TX_FEE)
                        succesful_transactions += 1
                        succesful_amount += amount
                        send_destination.last_payout_server_side = last_payout
                        send_destination.save()
                        user_settings.send_email_about_payout = True
                        user_settings.tx_id = res['transactionIds']
                        user_settings.save()
                    else:
                        failed_transactions += 1
                        failed_amount += amount
                        logger.warning('failed tx {}'.format(res))


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
                'tx_id': user.tx_id,
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

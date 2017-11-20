from ark_analytics import config
import arkdbtools.dbtools as arktool
import arkdbtools.config as arkinfo
import arkdbtools.utils as utils
import ark_delegate_manager.models
import console.info as info
import logging

logger = logging.getLogger(__name__)


def gen_payout_report(wallet):
    res = {}
    arktool.set_connection(
        host=config.CONNECTION['HOST'],
        database=config.CONNECTION['DATABASE'],
        user=config.CONNECTION['USER'],
        password=config.CONNECTION['PASSWORD']
    )

    arktool.set_delegate(
        address=config.DELEGATE['ADDRESS'],
        pubkey=config.DELEGATE['PUBKEY'],
    )

    height = arktool.Node.height()
    balance = arktool.Address.balance(wallet)
    payout_history = arktool.Address.payout(wallet)

    try:
        last_vote = arktool.Address.votes(wallet)[0]
        if last_vote.direction:
            delegate = ark_delegate_manager.models.ArkDelegates.objects.get(pubkey=last_vote.delegate).username
            vote_timestamp = last_vote.timestamp
        else:
            delegate = None
    except IndexError:
        last_vote = None
        delegate = None


    # initialize some variables
    total_reward = 0
    payout_result = {}
    share_percentage = None
    sender_delegate = 'unknown delegate'

    for tx in payout_history:
        total_reward += tx.amount

        # this is a fast try, as in 99% of the cases tx.senderId is in the database
        try:
            sender_delegate = ark_delegate_manager.models.ArkDelegates.objects.get(address=tx.senderId)
        except Exception:
            pass

        # this works for all delegates
        if tx.senderId in info.PAYOUT_DICT:
            for t in info.PAYOUT_DICT[tx.senderId]:
                if tx.timestamp < t:
                    share_percentage = info.PAYOUT_DICT[tx.senderId][t]

        # for dutchdelegate voters'
        if sender_delegate == 'dutchdelegate':
            for t in info.PAYOUT_DICT['AZse3vk8s3QEX1bqijFb21aSBeoF6vqLYE']:
                if tx.timestamp < t:
                    share_percentage = info.PAYOUT_DICT[tx.senderId][t]
            if share_percentage == 0.95:
                if vote_timestamp < 16247647 or tx.recipientId in info.EXCEPTIONS:
                    share_percentage = 0.96

        payout_result.update({
            tx.id:
                {'amount': tx.amount,
                 'timestamp': tx.timestamp,
                 'share': share_percentage,
                 'delegate': sender_delegate,
                 }
        })

    res.update({
        'succes': True,
        'node_height': height,
        'wallet': wallet,
        'current_delegate': delegate,
        'last_vote_timestamp': vote_timestamp,
        'balance': balance,
        'payout_history': payout_result,
        'total_stake_reward': total_reward
        }
    )
    return res


def gen_balance_report(wallet):
    res = {}
    arktool.set_connection(
        host=config.CONNECTION['HOST'],
        database=config.CONNECTION['DATABASE'],
        user=config.CONNECTION['USER'],
        password=config.CONNECTION['PASSWORD']
    )

    arktool.set_delegate(
        address=config.DELEGATE['ADDRESS'],
        pubkey=config.DELEGATE['PUBKEY'],
    )

    balance_over_time = arktool.Address.balance_over_time(wallet)
    balances = []
    for balance in balance_over_time:
        balances.append({
            'timestamp': arktool.utils.arkt_to_datetime(balance.timestamp),
            'balance': balance.amount/arkinfo.ARK
        })

    stake_amount = 0

    payouts = arktool.Address.payout(wallet)
    for i in payouts:
        stake_amount += i.amount/arkinfo.ARK

    height = arktool.Node.height()

    res.update({
        'success': True,
        'node_height': height,
        'wallet': wallet,
        'total_stake_reward': stake_amount,
        'balance_over_time': balances,
        })
    return res


def gen_roi_report(address):

    res = {}
    balance_history = arktool.Address.balance_over_time(address)
    payouts = arktool.Address.payout(address)

    for i in payouts:
        payout = {}
        for x in balance_history:
            balance_at_payout = x.amount
            if x.timestamp > payouts.timestamp:
                break
        payout.update({i.timestamp: {
            'payout_amount': i.amount,
            'balance_at_payout': balance_at_payout,
            'ark_timestamp': i.timestamp,
            'date': utils.arkt_to_datetime(i.timestamp),
            'ROI': i.amount / abs((balance_at_payout - i.amount))
        }
})
        res.update(payout)
    return res


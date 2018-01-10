from ark_analytics import config
import arkdbtools.dbtools as arktool
import arkdbtools.utils as utils
import ark_delegate_manager.models
import logging

logger = logging.getLogger(__name__)


def get_or_none(model, *args, **kwargs):
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        return None


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

    balance = arktool.Address.balance(wallet)
    payout_history = arktool.Address.payout(wallet)
    delegates = ark_delegate_manager.models.ArkDelegates.objects.all()
    height = arktool.Node.height()

    try:
        last_vote = arktool.Address.votes(wallet)[0]
        if last_vote.direction:
            delegate = delegates.get(pubkey=last_vote.delegate).username
            vote_timestamp = last_vote.timestamp
        else:
            delegate = None
            vote_timestamp = None
    except IndexError:
        vote_timestamp = None
        delegate = None


    # initialize some variables
    total_reward = 0
    payout_result = []
    share_ratio = None
    custom_share = None

    try:
        voter = ark_delegate_manager.models.VotePool.objects.select_related('customaddressexceptions').get(
            ark_address=wallet)

        custom_share = voter.customaddressexceptions.share_RANGE_IS_0_TO_1
    except Exception:
        pass

    for tx in payout_history:
        total_reward += tx.amount

        # this is a fast try, as in 99% of the cases tx.senderId is in the database
        try:
            delegate = delegates.get(address=tx.senderId)
            sender_delegate = delegate.username

            # if a new delegate arrives, or we haven't entered the data yet, this will lead to random errors.
            try:
                historic_share_percentages = delegate.share_percentages.json()
                for x in historic_share_percentages:
                    if tx.timestamp > x:
                        share_ratio = historic_share_percentages[x]
            except Exception:
                share_ratio = 'N.A.'
        except Exception:
            sender_delegate = 'N.A.'

        # for dutchdelegate voters'
        if sender_delegate == 'dutchdelegate' and vote_timestamp:
            if tx.timestamp < 16247647:
                share_ratio = 1
            elif vote_timestamp < 16247647:
                share_ratio = 0.96
            elif custom_share:
                share_ratio = custom_share
            else:
                share_ratio = 0.95

        payout_result.append({
            'amount': tx.amount,
            'timestamp': tx.timestamp,
            'id': tx.id,
            'share': share_ratio,
            'delegate': sender_delegate,
            })

    res.update({
        'succes': True,
        'height': height,
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
            'timestamp': balance.timestamp,
            'balance': balance.amount
        })

    stake_amount = 0

    payouts = arktool.Address.payout(wallet)
    for i in payouts:
        stake_amount += i.amount

    res.update({
        'success': True,
        'wallet': wallet,
        'total_stake_reward': stake_amount,
        'balance_over_time': balances,
        })
    return res


def gen_roi_report(address):

    res = {}
    balance_history = arktool.Address.balance_over_time(address)
    payouts = arktool.Address.payout(address)
    payout = []
    for i in payouts:
        for x in balance_history:
            if x.timestamp > i.timestamp:
                balance_at_payout = x.amount
                break
        payout.append({
            'payout_amount': i.amount,
            'balance_at_payout': balance_at_payout,
            'ark_timestamp': i.timestamp,
            'date': utils.arkt_to_datetime(i.timestamp),
            'ROI': i.amount / abs((balance_at_payout - i.amount))
        })

    res.update({'payout': payout})


    stake_amount = 0
    payouts = arktool.Address.payout(address)
    for i in payouts:
        stake_amount += i.amount

    res.update({
        'total_stake_reward': stake_amount
    })

    print(res)

    return res


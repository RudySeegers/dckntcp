from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile
import ark_delegate_manager.models
from .forms import UserForm
from django.forms.models import inlineformset_factory
from django.core.exceptions import PermissionDenied
from graphos.renderers.gchart import LineChart
from graphos.sources.simple import SimpleDataSource
import datetime
import logging
from . import info
from delegatewebapp.tokens import gen_ark_token, gen_kapu_token
from . import config
import arkdbtools.dbtools as arktool
import arkdbtools.config as arkinfo
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


@login_required(login_url='/login/')
def sidebar_context(request):
    current_user = User.objects.get(username=request.user.username)

    arkmainwallet = current_user.user.main_ark_wallet
    arkmaintag = current_user.user.main_ark_tag

    arkreceivemain = current_user.user.receiving_ark_address
    arkreceivemaintag = current_user.user.receiving_ark_address_tag
    logger.critical('{0}, {1}, {2}, {3}'.format(arkmainwallet, arkmaintag, arkreceivemain, arkreceivemaintag))

    context = {
        'arkmainwallet': arkmainwallet,
        'arksecwallet': arkreceivemain,
        'arksectag': arkreceivemaintag,
        'arkmaintag': arkmaintag,
    }

    return context


def saved(request):
    return render(request, 'console/saved.html')


def not_saved(request):
    return render(request, 'console/not_saved.html')


@login_required(login_url='/login/')
def console_wallet_history(request):
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

    context = sidebar_context(request)
    data_list = [
        ['date', 'Balance'],
        [datetime.datetime.now(), 0]
    ]
    data = SimpleDataSource(data=data_list)
    chart = LineChart(data, options={'title': 'Balance History'})

    context.update({'chart': chart})
    current_user = User.objects.get(username=request.user.username)

    wallet = current_user.user.main_ark_wallet
    balance_over_time = arktool.Address.balance_over_time(wallet)
    txhistory = arktool.Address.transactions(wallet)
    for tx in balance_over_time:
        data_list.append([arktool.utils.arkt_to_datetime(tx.timestamp), tx.amount / arkinfo.ARK])
    data = SimpleDataSource(data=data_list)
    chart = LineChart(data, options={'title': 'Balance History'})
    context.update({'chart': chart})
    tx_dic = {}
    for x in txhistory:
        if tx.senderId == wallet:
            amount = -x.amount
            txtype = 'Send'
            otherparty = tx.recipientId
        elif tx.recipientId == wallet:
            amount = x.amount
            txtype = 'Receive'
            otherparty = tx.senderId
        elif x.type == 2 or x.type == 3:
            txtype = 'Administrative Transaction'
            otherparty = None
        else:
            amount = x.amount
            txtype = x.type
            otherparty = tx.senderId

        tx_dic.update({x.id: {'amount': amount,
                              'type': txtype,
                              'otherparty': otherparty}})
    context.update({'tx_dic': tx_dic})
    return render(request, 'console/console_wallet_statistics.html', context)


@login_required()  # only logged in users should access this
def edit_user(request):
    # request user pk
    pk = request.user.pk

    # querying the User object with pk
    user = User.objects.get(pk=pk)

    # prepopulate UserProfileForm with retrieved user values from above.
    user_form = UserForm(instance=user)

    # The sorcery begins from here, see explanation below
    ProfileInlineFormset = inlineformset_factory(User, UserProfile,
                                                 fields=('main_ark_tag',
                                                         'main_ark_wallet',
                                                         'payout_frequency',
                                                         'receiving_ark_address',
                                                         'receiving_ark_address_tag',
                                                         'ark_send_to_second_address'))
    formset = ProfileInlineFormset(instance=user)
    username = user

    # Generate a verification token for receiving address verification
    arktoken = gen_ark_token(username)
    kaputoken = gen_kapu_token(username)

    if request.user.is_authenticated() and request.user.id == user.id:
        if request.method == "POST":
            user_form = UserForm(request.POST, request.FILES, instance=user)
            formset = ProfileInlineFormset(request.POST, request.FILES, instance=user)

            if user_form.is_valid():
                created_user = user_form.save(commit=False)
                formset = ProfileInlineFormset(request.POST, request.FILES, instance=created_user)

                if formset.is_valid():

                    created_user.save()
                    formset.save()
                    return HttpResponseRedirect('/console/update/saved')

        return render(request, "console/update2.html", {
            "noodle": pk,
            "noodle_form": user_form,
            "formset": formset,
            "arktoken": arktoken,
            "kaputoken": kaputoken,
        })
    else:
        raise PermissionDenied


@login_required(login_url='/login/')
def console_node(request):
    context = sidebar_context(request)
    dutchdelegateinfo = ark_delegate_manager.models.DutchDelegateStatus.objects.get(pk='main')

    dutchdelegate_ark_rank = dutchdelegateinfo.rank
    dutchdelegate_ark_productivity = dutchdelegateinfo.productivity
    dutchdelegate_total_ark_voted = dutchdelegateinfo.ark_votes
    dutchdelegatevoters = dutchdelegateinfo.voters

    context.update({
        'dutchdelegaterank': dutchdelegate_ark_rank,
        'totalarkvoted': dutchdelegate_total_ark_voted,
        'totalvoters': dutchdelegatevoters,
        'productivity': dutchdelegate_ark_productivity,
        'first': True
    })
    return render(request, "console/console_node.html", context)


@login_required(login_url='/login/')
def console_payout_report_ark_wallet_main(request):
    context = sidebar_context(request)
    address = context['arkwallet1']
    res = gen_payout_report(
        request=request,
        wallet=address,
        wallet_type='main_ark',)

    context.update(res)
    return render(request, "console/console_wallet_statistics.html", context)


@login_required(login_url='/login/')
def console_payout_report_ark_wallet_sec(request):
    context = sidebar_context(request)
    address = context['arkwallet2']
    res = gen_payout_report(
        request=request,
        wallet=address,
        wallet_type='sec_ark',)

    context.update(res)
    return render(request, "console/console_wallet_statistics.html", context)


@login_required(login_url='/login/')
def gen_balance_report(request, wallet, wallet_type):
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


@login_required(login_url='/login/')
def gen_payout_report(request, wallet, wallet_type):
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

    # create a placeholder chart in case everything with the node fails
    data_list = [
        ['date', 'Payout Amount'],
        [datetime.datetime.now(), 0]
    ]
    data = SimpleDataSource(data=data_list)
    chart = LineChart(data, options={'title': 'Payout History'})
    res.update({'chart': chart})
    try:
        if arktool.Node.check_node(100):
            arknode_status = True
        else:
            arknode_status = False
            logger.critical('Arknode is more than 100 blocks behind')
        balance = arktool.Address.balance(wallet)
        payout_history = arktool.Address.payout(wallet)
        last_vote = arktool.Address.votes(wallet)[0]
        height = arktool.Node.height()
        logger.info('balance {0}  payout_history {1}   lastvote {2}   height  {3}'.format(balance, payout_history, last_vote, height))
    except Exception:
        logger.exception('error in obtaining ark-data in gen_payout_report')
        return res

    # unpack lastvote
    vote_timestamp = last_vote.timestamp
    if last_vote.direction:
        delegate = ark_delegate_manager.models.ArkDelegates.objects.get(pubkey=last_vote.delegate).username
    else:
        delegate = None

    if delegate == 'dutchdelegate' and wallet_type == 'main_ark':
            try:
                builduppayout = ark_delegate_manager.models.VotePool.objects.get(ark_address=wallet).payout_amount
            except Exception:
                pass
    else:
        builduppayout = None

    # initialize some variables
    total_reward = 0
    payout_result = []
    share_p = 'not available'

    for tx in payout_history:
        total_reward += tx.amount
        data_list.append([arktool.utils.arkt_to_datetime(tx.timestamp), tx.amount/arkinfo.ARK])
        if tx.senderId in info.DELEGATE_DIC:
            sender_delegate = info.DELEGATE_DIC[tx.senderId]['username']

        # this works for all delegates
        if tx.senderId in info.PAYOUT_DICT:
            for t in info.PAYOUT_DICT[tx.senderId]:
                if tx.timestamp < t:
                    share_percentage = info.PAYOUT_DICT[tx.senderId][t]
                    share_p = str(int(100 * share_percentage)) + '%'

        # for dutchdelegate voters
        if sender_delegate == 'dutchdelegate':
            for t in info.PAYOUT_DICT['AZse3vk8s3QEX1bqijFb21aSBeoF6vqLYE']:
                if tx.timestamp < t:
                    share_percentage = info.PAYOUT_DICT[tx.senderId][t]
            if share_percentage == 0.95:
                if vote_timestamp < 16247647 or tx.recipientId in info.EXCEPTIONS:
                    share_percentage = 0.96
            share_p = str(int(100*share_percentage)) + '%'

        payout_result.append(
            {'amount': tx.amount/arkinfo.ARK,
             'time': arktool.utils.arkt_to_datetime(tx.timestamp),
             'share': share_p,
             'delegate': sender_delegate,
             })
    payout_result.reverse()

    if vote_timestamp < 16247647 and delegate == 'dutchdelegate' or wallet in info.EXCEPTIONS:
        status = 'Early adopter'
    elif delegate == 'dutchdelegate':
        status = 'Active voter'
    else:
        status = None

    data = SimpleDataSource(data=data_list)
    chart = LineChart(data, options={'title': 'Payout History'})

    res.update({
        'current_delegate': delegate,
        'wallet': wallet,
        'balance': 'Ѧ' + str(balance/arkinfo.ARK),
        'tx_history': payout_result,
        'timestamp_vote': vote_timestamp,
        'chart': chart,
        'total_reward': 'Ѧ' + str(total_reward/arkinfo.ARK),
        'height': height,
        'info': None,
        'status': status,
        'builduppayout': builduppayout,
        'arknodestatus': arknode_status
        })

    return res


@login_required(login_url='/login/')
def delegate_report(request):
    context = sidebar_context(request)
    delegate_dic = {}
    delegates = ark_delegate_manager.models.ArkDelegates.objects.all()
    for i in delegates:
        delegate_dic.update({
            'username': i.username,
            'rank': i.rank,
            'voters': i.voters,
            'productivity': i.productivity,
        })
    context.update({'delegates': delegate_dic})
    return render(request, 'console/delegate_report.html', context)



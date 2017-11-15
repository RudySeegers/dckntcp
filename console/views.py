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
import ark_delegate_manager.constants
logger = logging.getLogger(__name__)


def saved(request):
    """ if a user has succefully changed settings, this page is displayed """
    return render(request, 'console/saved.html')


def not_saved(request):
    """ if a user has not saved the page, this page is displayed """
    return render(request, 'console/not_saved.html')


@login_required()
def edit_user(request):
    """ used to render the wallet settings page"""
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
                                                         # 'receiving_ark_address',
                                                         # 'receiving_ark_address_tag',
                                                         # 'ark_send_to_second_address'
                                                         ))
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
def sidebar_context(request):
    """ generates the initial context needed to render consolebase.html """
    current_user = User.objects.get(username=request.user.username)

    arkmainwallet = current_user.user.main_ark_wallet
    arkmaintag = current_user.user.main_ark_tag

    arkreceivemain = current_user.user.receiving_ark_address
    arkreceivemaintag = current_user.user.receiving_ark_address_tag

    context = {
        'arkmainwallet': arkmainwallet,
        'arksecwallet': arkreceivemain,
        'arksectag': arkreceivemaintag,
        'arkmaintag': arkmaintag,
        'error': True
    }

    return context


@login_required(login_url='/login/')
def console_node(request):
    """ renders the initial landing page of the console, displaying the
    current delegates ran by dutchdelegate

    also sets session variables """
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
        'first': True,
        'error': False,
    })

    """setting some session statistics here"""
    request.session['arkmainwallet'] = context['arkmainwallet']
    request.session['arkmaintag'] = context['arkmaintag']
    request.session['arksecwallet'] = context['arksecwallet']
    request.session['arksectag'] = context['arksectag']

    # this is used to determine what wallet to generate reports on.
    # if None/not exists, arkmainwallet is used automatically
    request.session['current_wallet_view'] = None

    return render(request, "console/console_node.html", context)


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
    context.update({'tx_dic': tx_dic,
                    'error': False})
    return render(request, 'console/console_wallet_statistics.html', context)


@login_required(login_url='/login/')
def console_payout_report_ark_wallet_main(request):
    context = sidebar_context(request)
    address = context['arkmainwallet']
    wallettag = None
    try:
        wallettag = context['arkmaintag']
    except Exception:
        pass

    res = gen_payout_report(
        request=request,
        wallet=address,
        wallet_type='main_ark',)

    context.update(res)
    context.update({'wallettag': wallettag})
    return render(request, "console/console_wallet_statistics.html", context)


@login_required(login_url='/login/')
def console_payout_report_ark_wallet_sec(request):
    context = sidebar_context(request)
    address = context['arksecwallet']
    wallettag = None
    try:
        wallettag = context['arksectag']
    except Exception:
        pass

    res = gen_payout_report(
        request=request,
        wallet=address,
        wallet_type='sec_ark',)

    context.update(res)
    context.update({'wallettag': wallettag})

    return render(request, "console/console_wallet_statistics.html", context)


@login_required(login_url='/login/')
def console_balance_report_ark_wallet_sec(request):
    context = sidebar_context(request)
    address = context['arksecwallet']
    wallettag = None
    try:
        wallettag = context['arksectag']
    except Exception:
        pass
    res = gen_balance_report(request, address)
    context.update(res)
    context.update({'wallettag': wallettag})
    return render(request, 'console/console_wallet_balance.html', context)


@login_required(login_url='/login/')
def console_balance_report_ark_wallet_main(request):
    context = sidebar_context(request)
    address = context['arkmainwallet']
    wallettag = None
    try:
        wallettag = context['arkmaintag']
    except Exception:
        pass
    res = gen_balance_report(request, address)
    context.update(res)
    context.update({'wallettag': wallettag})
    return render(request, 'console/console_wallet_balance.html', context)


@login_required(login_url='/login/')
def gen_balance_report(request, wallet):
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
    data_list = [['date', 'Balance']]
    balances = []
    for balance in balance_over_time:
        data_list.append([arktool.utils.arkt_to_datetime(balance.timestamp).strftime('%d/%m/%Y'), balance.amount/arkinfo.ARK])
        balances.append({'timestamp': arktool.utils.arkt_to_datetime(balance.timestamp),
                         'balance': balance.amount/arkinfo.ARK})

    data = SimpleDataSource(data=data_list)
    chart = LineChart(data, options={'title': 'Balance History'})
    stake_amount = 0

    payouts = arktool.Address.payout(wallet)
    for i in payouts:
        stake_amount += i.amount/arkinfo.ARK

    res.update({'chart': chart,
                'stakeamount': stake_amount,
                'balances': balances,
                'error': False,
                'wallet': wallet})
    return res


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

    try:
        balance = arktool.Address.balance(wallet)
        payout_history = arktool.Address.payout(wallet)
        last_vote = arktool.Address.votes(wallet)[0]
        height = arktool.Node.height()
    except Exception:
        logger.exception('error in obtaining ark-data in gen_payout_report')
        return res

    # unpack lastvote
    vote_timestamp = last_vote.timestamp
    if last_vote.direction:
        delegate = ark_delegate_manager.models.ArkDelegates.objects.get(pubkey=last_vote.delegate).username
    else:
        delegate = None

    builduppayout = 0
    try:
        builduppayout = ark_delegate_manager.models.VotePool.objects.get(ark_address=wallet).payout_amount
    except Exception:
        pass

    # initialize some variables
    total_reward = 0
    payout_result = []
    share_p = 'not available'
    data_list = [['date', 'Payout amount']]
    sender_delegate = 'unknown delegate'

    for tx in payout_history:
        total_reward += tx.amount
        data_list.append([arktool.utils.arkt_to_datetime(tx.timestamp).strftime('%d/%m/%Y'), tx.amount/arkinfo.ARK])

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
             'time': arktool.utils.arkt_to_datetime(tx.timestamp).strftime('%d/%m/%Y'),
             'share': share_p,
             'delegate': sender_delegate,
             })
    payout_result.reverse()

    if vote_timestamp < 16247647 and delegate == 'dutchdelegate' or wallet in ark_delegate_manager.constants.PAYOUT_EXCEPTIONS:
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
        'builduppayout': 'Ѧ' + str(builduppayout/arkinfo.ARK),
        'error': False,
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



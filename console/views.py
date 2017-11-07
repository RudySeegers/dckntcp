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
import hashlib
from . import info
from delegatewebapp.tokens import gen_ark_token, gen_kapu_token
from . import config
import arkdbtools.dbtools as arktool
import arkdbtools.config as arkinfo

def saved(request):
    return render(request, 'console/saved.html')


def not_saved(request):
    return render(request, 'console/not_saved.html')


@login_required(login_url='/login/')
def console_ark_main(request):
    return console(request, arkwalletmain=True)


@login_required(login_url='/login/')
def console_ark_receive(request):
    return console(request, arkwalletmain=False)


@login_required(login_url='/login/')
def console(request, arkwalletmain):

    # todo replace this function with ardbtools.utils.arkt_to_datetime in next arkdbtools release
    def arkt_to_datetime(ark_timestamp):
        gen = datetime.datetime(2017, 3, 21, 15, 55, 44)
        return gen + datetime.timedelta(seconds=ark_timestamp)

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
    current_user = User.objects.get(username=request.user.username)

    # basic context for the sidebar nav
    context = sidebar_context(request)


    # if the an error occurs or something, at least an empty graph is displayed
    data_list = [
        ['date', 'Payout Amount'],
        [datetime.datetime.now(), 0]
    ]
    data = SimpleDataSource(data=data_list)
    chart = LineChart(data, options={'title': 'Payout History'})
    height = arktool.Node.height()
    wallettag = None
    context.update({
        'wallettag': wallettag,
        'current_delegate': 'not available',
        'wallet': current_user.user.main_ark_wallet,
        'balance': None,
        'tx_history': None,
        'timestamp_vote': None,
        'chart': chart,
        'total_reward': None,
        'height': height
    })

    try:
        if arkwalletmain:
            wallet = current_user.user.main_ark_wallet
            try:
                wallettag = current_user.user.main_ark_tag
            except Exception:
                pass
        else:
            wallet = current_user.user.receiving_ark_address
            try:
                wallettag = current_user.user.receiving_ark_address_tag
            except Exception:
                pass

        balance = arktool.Address.balance(wallet)
        payout_history = arktool.Address.payout(wallet)
        last_vote = arktool.Address.votes(wallet)[0]

        # last_vote could be an unvote, so lets format to make sure we don't display an unvoted delegate
        if last_vote.direction:
            vote_timestamp = last_vote.timestamp
            delegate = last_vote.delegate

            for i in info.DELEGATE_DIC:
                if info.DELEGATE_DIC[i]['pubkey'] == delegate:
                    delegate = info.DELEGATE_DIC[i]['username']
        else:
            vote_timestamp = float('inf')
            delegate = 'No delegate is currently voted by this account'

        total_reward = 0
        data_list = [['date', 'Payout Amount']]
        payout_result = []
        share_percentage = 'Not available'

        # calculate total staking reward and build data for graph
        # modify the payouts to include share percentages:

        for tx in payout_history:
            total_reward += tx.amount
            data_list.append([arkt_to_datetime(tx.timestamp), tx.amount/arkinfo.ARK])
            if tx.senderId in info.DELEGATE_DIC:
                sender_delegate = info.DELEGATE_DIC[tx.senderId]['username']

            # this works for all delegates
            if tx.senderId in info.PAYOUT_DICT:
                for t in info.PAYOUT_DICT[tx.senderId]:
                    if tx.timestamp < t:
                        share_percentage = info.PAYOUT_DICT[tx.senderId][t]

            # for dutchdelegate voters
            if sender_delegate == 'dutchdelegate':
                for t in info.PAYOUT_DICT['AZse3vk8s3QEX1bqijFb21aSBeoF6vqLYE']:
                    if tx.timestamp < t:
                        share_percentage = info.PAYOUT_DICT[tx.senderId][t]
                if share_percentage == 0.95:
                    if vote_timestamp < 16247647 or tx.recipientId in info.EXCEPTIONS:
                        share_percentage = 0.96
            try:
                share_percentage = str(int(100*share_percentage)), '%'
            except Exception:
                pass
            payout_result.append(
                {'amount': tx.amount/arkinfo.ARK,
                 'time': arkt_to_datetime(tx.timestamp),
                 'share': share_percentage,
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

        print(wallettag)
        context.update({
            'wallettag': wallettag,
            'current_delegate': delegate,
            'wallet': wallet,
            'balance': 'Ѧ' + str(balance/arkinfo.ARK),
            'tx_history': payout_result,
            'timestamp_vote': vote_timestamp,
            'chart': chart,
            'total_reward': 'Ѧ' + str(total_reward/arkinfo.ARK),
            'height': height,
            'info': None,
            'status': status
            })
    except Exception:
        pass
    if not context['balance'] and not context['tx_history']:
        context['info'] = True
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
                                                         'receiving_ark_address_tag',
                                                         'receiving_ark_address',
                                                         'ark_send_to_second_address'))
    formset = ProfileInlineFormset(instance=user)
    username = user

    # Generate a verification token for receiving address verification
    ark_address = UserProfile.main_ark_wallet
    kapuaddress = 'random'
    arktoken = gen_ark_token(username, ark_address)
    kaputoken = gen_kapu_token(username, kapuaddress)
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
def console_first(request):
    context = sidebar_context(request)
    return render(request, "console/console_1.html", context)


def sidebar_context(request):
    current_user = User.objects.get(username=request.user.username)


    arkmainwallet = current_user.user.main_ark_wallet
    arkreceivemain = current_user.user.receiving_ark_address
    arkreceivemaintag = current_user.user.receiving_ark_address_tag
    arkmaintag = current_user.user.main_ark_tag

    ark_wallet_1 = None
    ark_wallet_2 = None

    if not arkmaintag:
        ark_wallet_1 = arkmainwallet
    else: ark_wallet_1 = arkmaintag

    if arkreceivemain:
        ark_wallet_2 = arkreceivemain
        if arkreceivemaintag:
            ark_wallet_2 = arkreceivemaintag

    total_supported_arkwallets = ark_wallet_1, ark_wallet_2

    kapuwallets = None
    oxywallets = None
    shiftwallets = None

    dutchdelegateinfo = ark_delegate_manager.models.DutchDelegateStatus.objects.get(pk='main')

    dutchdelegate_ark_rank = dutchdelegateinfo.rank
    dutchdelegate_ark_productivity = dutchdelegateinfo.productivity
    dutchdelegate_total_ark_voted = dutchdelegateinfo.ark_votes
    dutchdelegatevoters = dutchdelegateinfo.voters



    context = {
        'arkwallet1': ark_wallet_1,
        'arkwallet2': ark_wallet_2,
        'kapuwallets': kapuwallets,
        'oxywallets': oxywallets,
        'shiftwallets': shiftwallets,
        'dutchdelegaterank': dutchdelegate_ark_rank,
        'totalarkvoted': dutchdelegate_total_ark_voted,
        'totalvoters': dutchdelegatevoters,
        'productivity': dutchdelegate_ark_productivity,
    }

    return context

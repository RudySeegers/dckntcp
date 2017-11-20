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
import ark_analytics.analytic_functions
import django.core.exceptions as django_exceptions
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
def payout_report(request, ark_address):
    context = sidebar_context(request)
    context.update({'error': False})

    request.session['current_wallet'] = ark_address

    # check if we have a wallet tag
    request.session['current_tag'] = None
    if ark_address == request.session['arkmainwallet']:
        request.session['current_tag'] = request.session['arkmaintag']
    elif request.session['arksecwallet']:
        request.session['current_tag'] = request.session['arksectag']

    res = ark_analytics.analytic_functions.gen_payout_report(ark_address)
    context.update(res)
    try:
        voter = ark_delegate_manager.models.VotePool.objects.get(ark_address=ark_address)
        builduppayout = voter.payout_amount
        context.update({'builduppayout': builduppayout})
    except django_exceptions.ObjectDoesNotExist:
        context.update({'error': True})

    data_list = [['date', 'Payout Amount']]
    for i in context['payout_history']:
        data_list.append([
            arktool.utils.arkt_to_datetime(i['timestamp']).strftime('%d/%m/%Y'),
            i['amount']/arkinfo.ARK
        ])
    data = SimpleDataSource(data=data_list)
    chart = LineChart(data, options={'title': 'Payout History'})
    context.update({'chart': chart})

    #display their dutchdelegate specific status:
    status = None
    if context['current_delegate'] == 'dutchdelegate':
        status = 'Regular voter'
        if context['last_vote_timestamp'] < ark_delegate_manager.constants.CUT_OFF_EARLY_ADOPTER:
            status = 'Early Adopter'
        else:
            try:
                res = ark_delegate_manager.models.EarlyAdopterExceptions.objects.get(ark_address)
                if res:
                    status = 'Early Adopter'
            except Exception:
                pass
    context.update({'status': status})

    # converting context variables to correct units
    for i in context['payout_history']:
        i['time'] = arktool.utils.arkt_to_datetime(i['timestamp'])
        i['amount'] = i['amount'] / arkinfo.ARK
        if i['share']:
            i['share'] = str(i['share'] * 100) + '%'
        else:
            i['share'] = 'Not available'


    context['payout_history'].reverse()
    context['balance'] = context['balance'] / arkinfo.ARK
    context['builduppayout'] = context['balance'] / arkinfo.ARK
    context['total_stake_reward'] = context['total_stake_reward'] / arkinfo.ARK

    return render(request, "console/console_wallet_statistics.html", context)


@login_required(login_url='/login/')
def balance_report(request, ark_address):
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
    context['error'] = False
    res = ark_analytics.analytic_functions.gen_balance_report(ark_address)
    context.update(res)

    # generate a chart and format balances with appropriate units
    data_list = [['date', 'Balance']]
    for i in context['balance_over_time']:
        i['time'] = arktool.utils.arkt_to_datetime(i['timestamp'])
        i['balance'] = i['balance'] / arkinfo.ARK
        data_list.append([
            i['time'].strftime('%d/%m/%Y'),
            i['balance']
        ])

    context['balance_over_time'].reverse()
    data = SimpleDataSource(data=data_list)
    chart = LineChart(data, options={'title': 'Balance History'})
    context.update({
        'chart': chart,
    })

    return render(request, 'console/console_wallet_balance.html', context)


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



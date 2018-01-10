from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from console.models import UserProfile
import ark_delegate_manager.models
from console.forms import SettingsForm
from django.core.exceptions import PermissionDenied
from graphos.renderers.gchart import LineChart
from graphos.sources.simple import SimpleDataSource
import logging
from delegatewebapp.tokens import gen_ark_token, gen_kapu_token
from . import config
import arkdbtools.dbtools as arktool
import arkdbtools.config as arkinfo
import ark_delegate_manager.constants
import ark_analytics.analytic_functions
import django.core.exceptions as django_exceptions
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
import datetime
logger = logging.getLogger(__name__)


def saved(request):
    """ if a user has succefully changed settings, this page is displayed """
    return render(request, 'console/saved.html')


def not_saved(request):
    """ if a user has not saved the page, this page is displayed """
    return render(request, 'console/not_saved.html')


@login_required()
def render_settings(request):
    """ used to render the wallet settings page, each form is validated by an individual view funtion"""
    context = sidebar_context(request)

    # request user pk
    pk = request.user.pk

    # querying the User object with pk
    user = User.objects.get(pk=pk)
    userprofile=UserProfile.objects.get(user=user)

    # prepopulate all forms  with retrieved user values from above.
    settingsform = SettingsForm(instance=userprofile)
    passwordform = PasswordChangeForm(request.user)
    # Generate a verification token for receiving address verification
    arktoken = gen_ark_token(user)
    if request.method == "GET":
        context.update({
            "error": False,
            "formset": settingsform,
            "passwordform": passwordform,
            "arktoken": arktoken,
        })
        return render(request, "console/update2.html", context)


@login_required(login_url='/login/')
def save_settings(request):

    # request user pk
    pk = request.user.pk

    # querying the User object with pk
    user = User.objects.get(pk=pk)

    if request.user.is_authenticated and request.user.id == user.id:
        if request.method == "POST":
            settings = SettingsForm(
                data=request.POST,
            )

            if settings.is_valid():
                settings_form_object = settings.save(commit=False)
                settings_form_object.user = user
                settings_form_object.save()
                messages.success(request, message='Saved your changes successfully.')
                return HttpResponseRedirect('/console/update/')
            else:
                error = 'Oops, something went wrong. (hint, check if your Ark address is valid.)'
                messages.error(request, message=error)
                return HttpResponseRedirect('/console/update/')
        else:
            raise PermissionDenied


@login_required(login_url='/login/')
def save_account_settings(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('/console/update')
        else:
            error = [form.error_messages[i] for i in form.error_messages]
            messages.error(request, message=error)
            return redirect('/console/update')


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
        status = voter.status
        if voter.blacklisted:
            return render(request, 'console/blacklisted.html', {
                'address': voter.address
            })

        builduppayout = voter.payout_amount/arkinfo.ARK
        context.update({
            'builduppayout': builduppayout,
            'status': status
             })
    except django_exceptions.ObjectDoesNotExist:
        context.update({'error': True})


    data_list = [['date', 'Payout Amount']]

    # converting context variables to correct units
    for i in context['payout_history']:
        i['time'] = arktool.utils.arkt_to_datetime(i['timestamp'])
        i['amount'] = i['amount'] / arkinfo.ARK

        data_list.append([
            i['time'],
            i['amount']
        ])
        if type(i['share']) == float or type(i['share']) == int:
            i['share'] = str(i['share'] * 100) + '%'

    # incase no payouts have occured yet, this will render an empty graph
    if len(data_list) == 1:
        data_list.append([
            datetime.datetime.today(),
            0])

    data = SimpleDataSource(data=data_list)
    chart = LineChart(data, options={'title': 'Payout History'})
    context.update({'chart': chart})
    try:
        context['payout_history'].reverse()
        context['balance'] = context['balance'] / arkinfo.ARK
        context['total_stake_reward'] = context['total_stake_reward'] / arkinfo.ARK
        context['error'] = False
    except Exception:
        context['error'] = True

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

    # incase no payouts have occured yet, this will render an empty graph
    if len(data_list) == 1:
        data_list.append([
            datetime.datetime.today(),
            0])

    context['balance_over_time'].reverse()
    context['total_stake_reward'] = context['total_stake_reward']/arkinfo.ARK

    data = SimpleDataSource(data=data_list)
    chart = LineChart(data, options={'title': 'Balance History'})
    context.update({
        'chart': chart,
    })

    return render(request, 'console/console_wallet_balance.html', context)

@login_required(login_url='/login/')
def roi_report(request, ark_address):
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

    res = ark_analytics.analytic_functions.gen_roi_report(ark_address)
    context.update(res)

    data_list = [['date', 'Balance']]
    for i in context['payout']:
        i['ROI'] = round(100*i['ROI'], 3)
        i['payout_amount'] /= arkinfo.ARK
        i['balance_at_payout'] /= arkinfo.ARK


        data_list.append([
            i['date'].strftime('%d/%m/%Y'),
            i['ROI']
        ])

    # incase no payouts have occured yet, this will render an empty graph
    if len(data_list) == 1:
        data_list.append([
            datetime.datetime.today(),
            0])

    data = SimpleDataSource(data=data_list)
    chart = LineChart(data, options={'title': 'Balance History'})
    context.update({
        'chart': chart,
    })

    context['error'] = False

    return render(request, 'console/console_roi_report.html', context)

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



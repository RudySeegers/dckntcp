"""We prebuild payout reports to decrease loading times for users."""


from django_cron import CronJobBase, Schedule
import console.models
import ark_delegate_manager.custom_functions as fnc
import ark_analytics.analytic_functions as anal
import ark_analytics.models
import json
import logging

logger = logging.getLogger(__name__)


class CreateVoteReports(CronJobBase):
    RUN_EVERY_MINS = 1
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ark_delegate_manager.create_vote_reports'

    def do(self):
        fnc.set_lock(name='CreateVoteReports')
        for user in console.models.UserProfile.objects.all():
            try:
                payout_report = json.dumps(anal.gen_payout_report(wallet=user.address))
                balance_report = json.dumps(anal.gen_balance_report(wallet=user.address))

                ark_analytics.models.PayoutReports.objects.update_or_create(
                    address=user.address,
                    payout_report=payout_report,
                    balance_report=balance_report
                    )
            except Exception:
                logger.exception('generating reports failed')

        fnc.release_lock(name='CreateVoteReports')
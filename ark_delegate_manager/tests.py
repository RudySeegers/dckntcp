from django.test import TestCase


# Create your tests here.


class ReporterTests(TestCase):
    def test_raven_and_sentry(self):
        import logging
        logger = logging.getLogger(__name__)
        constant = 1
        string = 'string'
        logger.error('Testerror to check if logger works', exc_info=True, extra={
            'value': constant,
            'test': string
        })


class PayoutFunctionsTests(TestCase):
    def setUp(self):
        import arkdbtools.dbtools as ark
        from . import config
        ark.set_connection(
            host=config.CONNECTION['HOST'],
            database=config.CONNECTION['DATABASE'],
            user=config.CONNECTION['USER'],
            password=config.CONNECTION['PASSWORD']
        )

        ark.set_delegate(
            address=config.DELEGATE['ADDRESS'],
            pubkey=config.DELEGATE['PUBKEY'],
        )

    def test_send(self):
        from . import payout_functions
        from django.conf import settings
        settings.DEBUG = True
        address = 'test'
        amount = 1
        # this test will not actually test if a transaction is sent on the Ark network,
        # just if testmode is working.
        self.assertTrue(payout_functions.send_tx(address, amount))

    def test_runpayments(self):
        from . import payout_functions
        from django.conf import settings
        settings.DEBUG = True
        import arkdbtools.dbtools as ark
        payouts, timestamp = ark.Delegate.trueshare()
        res = payout_functions.paymentrun(
            payout_dict=payouts,
            current_timestamp=timestamp
            )
        self.assertTrue(res)


class TestVerifyReceivingArkAddresses(TestCase):
    def test_verify_address_run(self):
        from . import payout_functions
        import console.models
        payout_functions.verify_address_run()
        test_address = 'AJwHyHAArNmzGfmDnsJenF857ATQevg8HY'
        obj = console.models.UserProfile.objects.get(main_ark_wallet=test_address)
        self.assertEquals(test_address, obj.main_ark_wallet)
        self.assertTrue(obj.receiving_ark_address_verified)


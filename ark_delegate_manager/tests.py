
from arky import api, core
import arkdbtools.config as constants
from requests.exceptions import ReadTimeout
from urllib3.exceptions import ReadTimeoutError
secret = ''

def send_tx(address, amount, vendor_field=''):
    try:
        tx = core.Transaction(
            amount=amount,
            recipientId=address,
            vendorField=vendor_field
        )
        tx.sign(secret)
        tx.serialize()
        result = api.sendTx(tx=tx, url_base='http://146.185.144.47:4001')
    except ReadTimeoutError:
        # we'll make a single retry in case of a ReadTimeOutError. We are sending the exact same TX hash to make
        # sure no double payouts occur
        result = api.sendTx(tx=tx, url_base='http://146.185.144.47:4001')
    if result['success']:
        return True

    return False

api.use('ark')
send_tx(address='AJ8nGFj9CVq3i4hb2CnxBoy41bUDhShJwr', amount=constants.ARK)

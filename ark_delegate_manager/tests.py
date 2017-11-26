from .payout_functions import set_lock_payment_run, ConcurrencyError, release_lock_payment_run
import _thread


for i in range(100):
    try:
        _thread.start_new_thread(set_lock_payment_run, ("Thread-{}".format(i)))
        print('succesfully set lock')
    except ConcurrencyError():
       print('failed to set lock for "Thread-{}".format(i)')

release_lock_payment_run()

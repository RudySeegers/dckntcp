from ark_delegate_manager.payout_functions import set_lock_payment_run, release_lock_payment_run
import _thread


release_lock_payment_run(name='testlock')

def test_race():
    try:
        set_lock_payment_run(name='testlock')
    except Exception as e:
        print('failed to set lock: {}'.format(e))


for i in range(5):
        _thread.start_new_thread(test_race, ())
release_lock_payment_run(name='testlock')

from ark_delegate_manager.custom_functions import set_lock, release_lock
import _thread


release_lock(name='testlock')

def test_race():
    try:
        set_lock(name='testlock')
    except Exception as e:
        print('failed to set lock: {}'.format(e))


for i in range(5):
        _thread.start_new_thread(test_race, ())
release_lock(name='testlock')

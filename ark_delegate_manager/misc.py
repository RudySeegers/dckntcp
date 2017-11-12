import arky.api
import arkdbtools.dbtools as ark_node
import arkdbtools.config as info
import arkdbtools.utils as utils
from arky import api
api.use('ark')
for i in utils.api_call(api.Delegate.getDelegates)['delegates']:
    print(i)

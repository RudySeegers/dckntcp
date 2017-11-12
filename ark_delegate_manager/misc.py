import arky.api
import arkdbtools.dbtools as ark_node
import arkdbtools.config as info


arky.api.use('ark')
print(arky.api.Delegate.getDelegates())

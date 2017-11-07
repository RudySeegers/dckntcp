import arky.api
import arkdbtools.dbtools as ark_node
import arkdbtools.config as info


arky.api.use('ark')
dutchdelegatestatus = arky.api.Delegate.getDelegate('dutchdelegate')
print(dutchdelegatestatus)
dutchdelegate_ark_rank = dutchdelegatestatus['delegate']['rate']
print(dutchdelegate_ark_rank)
dutchdelegate_ark_productivity = dutchdelegatestatus['delegate']['productivity']
print(dutchdelegate_ark_productivity)
dutchdelegate_total_ark_voted = int(dutchdelegatestatus['delegate']['vote']) / info.ARK
print(dutchdelegate_total_ark_voted)

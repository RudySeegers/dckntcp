from arky import api, cli
import json

api.use('ark')

delegates = api.Delegate.getDelegates()['delegates']

delegate_dic = {}
for i in delegates:
    delegate_dic.update({i['address']: {'username': i['username'],
                                        'pubkey': i['publicKey']}})

print(delegate_dic)




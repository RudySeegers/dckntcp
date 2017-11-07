import datetime


DELEGATE_DIC = {'ARAq9nhjCxwpWnGKDgxveAJSijNG8Y6dFQ': {'username': 'arkpool', 'pubkey': '02b1d2ea7c265db66087789f571fceb8cc2b2d89e296ad966efb8ed51855f2ae0b'},
                'ASvYCmBFTZW6R52SrZexQFwZbErKcLLSW9': {'username': 'boxpool', 'pubkey': '0226c1d974f21f9e0ec5bc7d2dcabdc481869b289c77f4f1b068ed154c5dd3e01e'},
                'AUdruJPoPruy58SSj2RmQR96CbxpyrdKbX': {'username': 'doom', 'pubkey': '027a9b5dc98c75902f871e889fb3076dd27b11e158a49e3915e0307ecd9781f51e'},
                'AGSZD47StY1DiHvA5Uf8f2MiU5892cFmsA': {'username': 'sharkpool', 'pubkey': '022bb6c5050444b24ba91b3959800c4df8c678a5d7293b4b43df17bffec03ae027'},
                'ASJBHz4JfWVUGDyN61hMMnW1Y4ZCTBHL1K': {'username': 'chris', 'pubkey': '027acdf24b004a7b1e6be2adf746e3233ce034dbb7e83d4a900f367efc4abd0f21'},
                'AXvBF7JoNyM6ztMrgr45KrqQf7LA7RgZhf': {'username': 'ravelou', 'pubkey': '021f277f1e7a48c88f9c02988f06ca63d6f1781471f78dba49d58bab85eb3964c6'},
                'AUrJhHwS6KLj9Q9dQdamALdjpco5v8jw2T': {'username': 'superstar', 'pubkey': '02a6b88567f86fa22d3c958f470c1645b3f65aa555e00c5bb0eecd2886eab80d34'},
                'AKdr5d9AMEnsKYxpDcoHdyyjSCKVx3r9Nj': {'username': 'biz_classic', 'pubkey': '020431436cf94f3c6a6ba566fe9e42678db8486590c732ca6c3803a10a86f50b92'},
                'ANwjGUcVbLXpqbBUWbjUBQWkr4MWVDuJu9': {'username': 'dr10', 'pubkey': '031641ff081b93279b669f7771b3fbe48ade13eadb6d5fd85bdd025655e349f008'},
                'AdBSvLKPp6pMp5ZDsxkgjFu6KeCokncSMk': {'username': 'rasputin', 'pubkey': '034682a4c4d2c8c0bc5f966dd422a83d2b433e212ef1f334f82cc3fe4676240933'},
                'ALLZ3TQKTaHm2Bte4SrXL9C5cS8ZovqFfZ': {'username': 'goose', 'pubkey': '03c5d32dedf5441b3aafb2e0c6ad3e5568bb0b3e822807b133e2276e014d830e3c'},
                'AHffXLGkqXgvBh2Z7qM4v3cvo2dCQd37w8': {'username': 'reconnico', 'pubkey': '0385e364f417e9a8de5621429283c0f121295d8bbcb4169bc8e5890a89f0300a44'},
                'AJiHx96wonWbauQNCcnEHA9ALNjmbu1Ztv': {'username': 'del', 'pubkey': '03d9ed6e7f29daf12ef925d4ce5753aade23c8cfd52a0427240fb30ad6ec232fed'},
                'Abi3CE3k7XzYGtLjG7toZ5fF31stSmW55H': {'username': 'quarkpool', 'pubkey': '027c550ecc71e4d9b832cf83c1c5c4d7c22dc43e3a451fea887c82a6ef55bf52fa'},
                'AQn38QrzwndyGMNPLDUmDniCr6VsCnwNwj': {'username': 'yin', 'pubkey': '03abd20e654fa87af4efcdbbb4a0dd82a01cf3e88e72269809b698d785b98b09b2'},
                'AHUzSzYLVhqJuXpPubmhdE2dD2otMBvLQZ': {'username': 'wes', 'pubkey': '0354319db3f22fb8d4588a09ebbb3e91631cbc2202ba58c69149b75c1a47eb7686'},
                'AQwTP4kT6rdE9ASyY3sbcMLyWKp4diKtjC': {'username': 'kolap', 'pubkey': '02b54f00d9de5a3ace28913fe78a15afcfe242926e94d9b517d06d2705b261f992'},
                'AKATy581uXWrbm8B4DTQh4R9RbqaWRiKRY': {'username': 'arkmoon', 'pubkey': '0232b96d57ac27f9a99242bc886e433baa89f596d435153c9dae47222c0d1cecc3'},
                'AKXmA2bs1ru4xCH8bDCDm3Yck3nhLCEYjd': {'username': 'bangomatic', 'pubkey': '03c85a134d79ecee00c9572fc95b4400edaf1d404d8e0edcc7265abaf6490faae9'},
                'AMvZYkTSMXCqFLPP4bxJyq84FfMg9m2V81': {'username': 'calidelegate', 'pubkey': '037b4730e7c63252912825510423487e9ee507e1a5719dfeef52187d8ababe3048'},
                'AKBUegoaAoSq3bepmXmzUL7XeEt6ScVM98': {'username': 'ghostfaceuk', 'pubkey': '0344f455358055213235a21eff6deffa4d8ded38e43b9103e10184cc4c108ee81c'},
                'AbEtS8VA4LA1wgJWf4wA3JKyZrfvimp4Ht': {'username': 'corsaro', 'pubkey': '0329e069d25bf0ede7e32bdade3107ede3e460cfb80404cf43348f42e8ceeca54f'},
                'ARVNmpr14oh1X3Ee31TVF4vQr2QmfXvbwE': {'username': 'samuray', 'pubkey': '024bd465c9671f6fa6d5b0c3f7debd10618c2b7089dbf71c109f4fe02d1a03dea7'},
                'AdVSe37niA3uFUPgCgMUH2tMsHF4LpLoiX': {'username': 'arkx', 'pubkey': '032fcfd19f0e095bf46bd3ada87e283720c405249b1be1a70bad1d5f20095a8515'},
                'AKmcaBfVepg8YwZxCb8gSYKWWNaeJxwu5d': {'username': 'criptodogg', 'pubkey': '034920a86224835ed039cbfdd6dbaf74061a750377126747c7ce68fd5ef8c8b9d4'},
                'ARKfan7iMEK3cn8QDWVzcKdCCpL4MkASHb': {'username': 'jamiec79', 'pubkey': '025631d7f863d2688443a14654e1b308c7585cb5f78563b3e785a978fdefff2c3e'},
                'AZzmCRP3Us7q4Pbyu3qCr2Dwq8vvuseLKa': {'username': 'pieface', 'pubkey': '026b87a3ad1c13adfc4256f5365f5e6251693a27b2293676db14690efce5acae6e'},
                'AKzB7dWkCsYnt4u9P4Sch6iKyZ7QnDjBav': {'username': 'acf', 'pubkey': '03e6397071866c994c519f114a9e7957d8e6f06abc2ca34dc9a96b82f7166c2bf9'},
                'AZM9qB6ujFLsmESuHKhrvnnk4NnsvxjBpG': {'username': 'ryano', 'pubkey': '032f2df8a6bae16b58172460149426dd6c1aa13ccb1bea0051081b1fc17f1befea'},
                'AZse3vk8s3QEX1bqijFb21aSBeoF6vqLYE': {'username': 'dutchdelegate', 'pubkey': '0218b77efb312810c9a549e2cc658330fcc07f554d465673e08fa304fa59e67a0a'},
                'AdaF5mb7Zpc47mFJXTy65e67XE9DQLaUXb': {'username': 'arkship', 'pubkey': '0371e0dabfd774b4f53fb9c5386a31ee4b3cb951529f18fdb5b8b7e21dbfb4b885'},
                'APRt1h4Mrimbjuqm8deiYpuX1wpaM7dfNb': {'username': 'pitbull', 'pubkey': '03dff448e2fe490aff1665da1e217f39ac8b6715e5ecfdfec20bc150da70ef5153'},
                'AdAftY6ZZQ4h6CoKgVDyY4ms2rGFzpHDPT': {'username': 'dafty', 'pubkey': '035845a4f1125ce10f4cbe8a271378b0004c5722874a72dc214044107e4b21b324'},
                'ATRjRVegVoAtfWbbuUsB35z5ruGBcuPJop': {'username': 'axi', 'pubkey': '037d3bb9ad6d44cc5ce3de3134367ae62688a941ba50c8b93787a5fa36dffb5f65'},
                'APVpLtN9NxsNMyhLucP4vmFHHyyV2QKx4t': {'username': 'digitron', 'pubkey': '0339a6bb2aff249cd13b55fce2442703a1d488bae343a22fa09bbff46a6a64c5e2'},
                'AaAy8BZkjV86YN7xUtZ35iwyXRMQKtKoAy': {'username': 'biz_private', 'pubkey': '02fa6902e91e127d6d3410f6abc271a79ae24029079caa0db5819757e3c1c1c5a4'},
                'AHazk56nvQ3isZrYkarJV1RPcDUrQocmfR': {'username': 'anamix', 'pubkey': '02a0ed5604868461a87639f58bd3a55f661774c3cbb705a735f58c50087f942c3d'},
                'AbUdMhk96FbzxH7vDYAwdyqUELmLopZV5x': {'username': 'bioly', 'pubkey': '02c0b645f19ab304d25aae3add139edd9f6ca9fd0d98e57a808100de0e93832181'},
                'AUycoaAHjReb1iYtGe4qWH5v7MJ95sjkvZ': {'username': 'arkgallery', 'pubkey': '03ca4edbdc4e83eb6f1b8780a532c74a3708d51f281b6bfb9a308d49c47d3ac90d'},
                'AXW2vq7bNvAJS7uRcZBdyRWca9Dehtr8ds': {'username': 'toad', 'pubkey': '031c110968941f29c76f3752d5752d5541cfe65f23f5d7f9115d2f4eb194f41c47'},
                'ALy9GoaRwC9HYxVCYfXVC3JmJCZ3c9q2CD': {'username': 'sharkark', 'pubkey': '03a08016096c48192211beef9f859278483fd0bf77e4a0f1b46d9627e366b003ec'},
                'Aasu14aTs9ipZdy1FMv7ay1Vqn3jPskA8t': {'username': 'jarunik', 'pubkey': '02c7455bebeadde04728441e0f57f82f972155c088252bf7c1365eb0dc84fbf5de'},
                'AL4o9fVfTQd4cTTh4SL8b8jUPTXt1KPGwA': {'username': 'forginator', 'pubkey': '0298e1bceff94716ca65914e31fbea0fba8e545d9a188dde902fc1d4fcd679f015'},
                'ARfDVWZ7Zwkox3ZXtMQQY1HYSANMB88vWE': {'username': 'arky', 'pubkey': '030da05984d579395ce276c0dd6ca0a60140a3c3d964423a04e7abe110d60a15e9'},
                'AMdPL5Br3nsWyJB4LCB5qZ9cYnKBdVXKJi': {'username': 'tibonos', 'pubkey': '02bd74ba354e4533cbbb0d03076622c15917e2e1d65fe4c4c8294d6b4c57d667b4'},
                'AR2iXnLRp9HuoT584m6tjNWLHGWdX8uuGK': {'username': 'doc', 'pubkey': '03cefbfa0c1c853084591b62a9aad0116029eaebdc27c2e3b811b1b0aebb928fc6'},
                'AJTVzJhvwWrb1UHLep1TwF2kT5LgaTDwZi': {'username': 'atreides_wannabe', 'pubkey': '031c660c85276df9457c041257723991aaad9e960618f57f6cd91601abebf6d775'},
                'APzMVrARso9qatWF5VPCyDTttBFKjcNccL': {'username': 'emotive_ark', 'pubkey': '035a0302ddd571bb821f6b069450814cb29fc927f14f146491fd5c9b3ab57d8ca8'},
                'ARESrXpca6ehHWyVkhh1wvDgAiNwpsA2VH': {'username': 'ares', 'pubkey': '02c44cc9787fae3ce5c8873ff541deadb86cd8ddb56a90dba37049ca6506d022f5'},
                'AJC9TuRXGxmqiCs3wmtt9CowfC8s2vMhEF': {'username': 'therock', 'pubkey': '023a4015f921d8d0248f40362db44e856769a7291224cbd8f2fc14d61be2138174'},
                'AZrMTx8CXHgueesybqsDmLkDo814hrtSb3': {'username': 'bbclubark', 'pubkey': '02cded5c40a4eb73d70eb903752839e74f7c1553e46597c2f1b6f27bac1966f429'}}

PAYOUT_DICT = {
    'ANwjGUcVbLXpqbBUWbjUBQWkr4MWVDuJu9':
    {
        float('inf'): 0.7,
        15577456: 0.6,

    },
   'AZse3vk8s3QEX1bqijFb21aSBeoF6vqLYE':
    {
        float('inf'): 0.95,
        16247647: 1,

    }
}

EXCEPTIONS = []

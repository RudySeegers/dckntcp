from django_cron import CronJobBase, Schedule
from relay_manager.models import RelayNodes
import dpostools.api
import logging

logger = logging.getLogger(__name__)


class CheckPeers(CronJobBase):
    RUN_EVERY_MINS = 60
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'relay_manager_check_peers'

    def do(self):
        """
        Check all relay nodes registered in the DB and report to sentry if one is significantly behind
        """

        MAX_DIF = 100

        arknetwork = dpostools.api.Network('Ark')

        # here we compile the info on all our nodes, + get the network height from ALL relay nodes.
        for node in RelayNodes.objects.all():
            if node.type == 'Ark':
                arknetwork.add_peer('http://{IP}:{PORT}'.format(
                    IP=node.ip,
                    PORT=node.port
                ))

        # status contains info on all our relay nodes
        status = arknetwork.status()

        # now we go over our registered nodes again and check their status
        for node in RelayNodes.objects.all():

            # we compare based on height (if they are significantly behind (i.e. 100 blocks = 800 seconds)
            height = status['peer_status'][node.ip]['height']
            if abs(int(height) - int(status['network_height'])) > MAX_DIF:
                logger.warning('Peer {PEER} is behind. Owner: {OWNER}, Email: {EMAIL}'.format(
                    PEER=node.ip,
                    OWNER=node.owner,
                    EMAIL=node.email,
                ))

            # and based on their own status, which they report as "ok".
            # sometimes a node doesn't realise on its own something is wrong.

            ok = status['peer_status'][node.ip]['status']

            if ok != 'ok':
                logger.warning('Peer {PEER} not ok. Owner: {OWNER}, Email: {EMAIL}'.format(
                    PEER=node.ip,
                    OWNER=node.owner,
                    EMAIL=node.email,
                ))


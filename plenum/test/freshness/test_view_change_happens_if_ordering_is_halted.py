import pytest

from plenum.test.delayers import ppDelay
from plenum.test.freshness.helper import has_freshness_instance_change
from plenum.test.helper import freshness
from plenum.test.node_request.helper import sdk_ensure_pool_functional
from plenum.test.stasher import delay_rules
from stp_core.loop.eventually import eventually

FRESHNESS_TIMEOUT = 5


@pytest.fixture(scope="module")
def tconf(tconf):
    with freshness(tconf, enabled=True, timeout=FRESHNESS_TIMEOUT):
        yield tconf


def test_view_change_happens_if_ordering_is_halted(looper, tconf, txnPoolNodeSet,
                                                   sdk_wallet_client, sdk_pool_handle):
    current_view_no = txnPoolNodeSet[0].viewNo
    for node in txnPoolNodeSet:
        assert node.viewNo == current_view_no

    def check_next_view():
        for node in txnPoolNodeSet:
            assert node.viewNo > current_view_no

    stashers = [n.nodeIbStasher for n in txnPoolNodeSet]
    with delay_rules(stashers, ppDelay()):
        looper.run(eventually(check_next_view, timeout=FRESHNESS_TIMEOUT * 3))

    assert sum(1 for node in txnPoolNodeSet if has_freshness_instance_change(node)) >= 3

    sdk_ensure_pool_functional(looper, txnPoolNodeSet, sdk_wallet_client, sdk_pool_handle)

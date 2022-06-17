import pytest

from autonet.core.objects import vlan as an_vlan

from autonet_cumulus.tasks import vlan as vlan_task


@pytest.mark.parametrize('test_vlan_id, test_show_dynamic, expected', [
    (88, False, [an_vlan.VLAN(id=88, admin_enabled=True)]),
    (None, False, [
        an_vlan.VLAN(id=71, admin_enabled=True),
        an_vlan.VLAN(id=72, admin_enabled=True),
        an_vlan.VLAN(id=88, admin_enabled=True),
        an_vlan.VLAN(id=100, admin_enabled=True),
        an_vlan.VLAN(id=250, admin_enabled=True),
    ]),
    (None, True, [
        an_vlan.VLAN(id=71, admin_enabled=True),
        an_vlan.VLAN(id=72, admin_enabled=True),
        an_vlan.VLAN(id=88, admin_enabled=True),
        an_vlan.VLAN(id=100, admin_enabled=True),
        an_vlan.VLAN(id=250, admin_enabled=True),
        an_vlan.VLAN(id=4001, admin_enabled=True),
        an_vlan.VLAN(id=4074, admin_enabled=True),
        an_vlan.VLAN(id=4086, admin_enabled=True)
    ]),
    (4074, False, []),
    (4074, True, [an_vlan.VLAN(id=4074, admin_enabled=True)])
])
def test_get_vlans(test_vlan_data, test_vlan_id,
                   test_show_dynamic, expected):
    vlans = vlan_task.get_vlans(test_vlan_data, 'bridge',
                                [x for x in range(4000, 4096)],
                                test_vlan_id,
                                test_show_dynamic)
    assert vlans == expected


@pytest.mark.parametrize('test_vlan, test_bridge, expected', [
    (an_vlan.VLAN(id=55), 'bridge', ['add bridge bridge vids 55']),
    (an_vlan.VLAN(id=10), 'vlan', ['add bridge vlan vids 10']),
])
def test_generate_create_vlan_commands(test_vlan, test_bridge, expected):
    commands = vlan_task.generate_create_vlan_commands(
        test_vlan, test_bridge)
    assert commands == expected


@pytest.mark.parametrize('test_vlan_id, test_bridge, expected', [
    (55, 'bridge', ['del bridge bridge vids 55']),
    (10, 'vlan', ['del bridge vlan vids 10']),
])
def test_generate_delete_vlan_commands(test_vlan_id, test_bridge, expected):
    commands = vlan_task.generate_delete_vlan_commands(
        test_vlan_id, test_bridge)
    assert commands == expected

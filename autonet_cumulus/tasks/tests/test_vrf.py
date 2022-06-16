import pytest

from autonet.core.objects import vrf as an_vrf

from autonet_cumulus.tasks import vrf as vrf_task


@pytest.mark.parametrize('test_vrf_name, expected', [
    (None, [
        an_vrf.VRF(name='TestCust1-Prod', ipv4=True, ipv6=True,
                   import_targets=[], export_targets=[]),
        an_vrf.VRF(name='connmgmt', ipv4=True, ipv6=True,
                   import_targets=[], export_targets=[]),
        an_vrf.VRF(name='green', ipv4=True, ipv6=True,
                   import_targets=[], export_targets=[]),
        an_vrf.VRF(name='mgmt', ipv4=True, ipv6=True,
                   import_targets=[], export_targets=[]),
        an_vrf.VRF(name='vrf-red', ipv4=True, ipv6=True,
                   import_targets=[], export_targets=[])
    ]),
    ('TestCust1-Prod', [
        an_vrf.VRF(name='TestCust1-Prod', ipv4=True, ipv6=True,
                   import_targets=[], export_targets=[])
    ])
])
def test_get_vrfs(test_ip_vrf_data, test_vrf_name, expected):
    vrfs = vrf_task.get_vrfs(test_ip_vrf_data, test_vrf_name)
    assert vrfs == expected


@pytest.mark.parametrize('test_vrf, expected', [
    (an_vrf.VRF(name='green'),
     ['add vrf green']),
    (an_vrf.VRF(name='magenta', ipv6=False, ipv4=True,
                import_targets=['65000:11'], export_targets=['65000:11'],
                route_distinguisher='198.18.0.1:11'),
     ['add vrf magenta']
     )
])
def test_generate_create_vrf_commands(test_vrf, expected):
    commands = vrf_task.generate_create_vrf_commands(test_vrf)
    assert commands == expected


def test_generate_delete_vrf_commands():
    expected = ['del vrf green']
    commands = vrf_task.generate_delete_vrf_commands('green')
    assert commands == expected

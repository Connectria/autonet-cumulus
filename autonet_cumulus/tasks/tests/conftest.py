import pytest

from autonet.core.objects import vxlan as an_vxlan


@pytest.fixture(autouse=True)
def flush_config():
    """
    Used to flush any cached config changes at the end of the test.
    """
    yield
    from autonet_cumulus.driver import config
    config.flush_cache()


@pytest.fixture
def test_int_data(test_show_int_data, request):
    """
    Returns a tuple of `int_name, int_data, subint_data`
    """
    unconfigured = {
        'iface_obj': {
            'lldp': None,
            'native_vlan': None,
            'dhcp_enabled': False,
            'description': '',
            'vlan': None,
            'asic': None,
            'mtu': '',
            'lacp': {
                'rate': '',
                'sys_priority': '',
                'partner_mac': '',
                'bypass': ''},
            'mac': '',
            'vlan_filtering': False,
            'min_links': '',
            'members': {},
            'counters': None,
            'ip_address': {
                'allentries': []},
            'vlan_list': [],
            'ip_neighbors': None},
        'linkstate': 'UNK',
        'summary': '',
        'connector_type': 'Unknown',
        'mode': 'NotConfigured',
        'speed': 'N/A'}
    subint = f"{request.param}-v0"
    if not request.param or request.param not in test_show_int_data:
        return request.param, unconfigured, None
    elif subint in test_show_int_data:
        return (request.param,
                test_show_int_data[request.param],
                test_show_int_data[subint])
    else:
        return (request.param,
                test_show_int_data[request.param],
                None)


@pytest.fixture
def test_show_int_data():
    # This is a stripped down version of what the device would actually
    # return.  Only data needed for testing is present.
    return {
        'TestCust1-Prod': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': 'f2:01:34:39:d1:47',
                'members': {},
                'min_links': '',
                'mtu': 65536,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'VRF',
            'speed': 'N/A',
            'summary': ''},
        'bond20': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '[an]',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '0',
                    'partner_mac': '0c:fe:87:e8:a9:4d',
                    'rate': '1',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:03',
                'members': {
                    'swp3': 'swp3'},
                'min_links': '1',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': '802.3ad',
            'speed': '1G',
            'summary': 'Bond Members: swp3(UP)'},
        'bridge': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:06',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': True,
                'vlan_list': '71-72,100,250,4001,4074,4086'},
            'linkstate': 'UP',
            'mode': 'Bridge/L2',
            'speed': 'N/A',
            'summary': ''},
        'connmgmt': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '62:2b:5d:02:2d:ac',
                'members': {},
                'min_links': '',
                'mtu': 65536,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'VRF',
            'speed': 'N/A',
            'summary': ''},
        'eth0': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': True,
                'ip_address': {
                    'allentries': ['172.20.4.9/26']},
                'ip_neighbors': {
                    'ipv4': ['0c:fe:87:0a:74:bf'],
                    'ipv6': []},
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:00',
                'members': {},
                'min_links': '',
                'mtu': 1500,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Mgmt',
            'speed': '1G',
            'summary': 'Master: mgmt(UP)\nIP: 172.20.4.9/26(DHCP)'},
        'green': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': 'c2:57:63:bd:7e:5b',
                'members': {},
                'min_links': '',
                'mtu': 65536,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'VRF',
            'speed': 'N/A',
            'summary': ''},
        'lo': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': ['127.0.0.1/8',
                                   '192.168.0.106/32',
                                   '::1/128']},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '00:00:00:00:00:00',
                'members': {},
                'min_links': '',
                'mtu': 65536,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Loopback',
            'speed': 'N/A',
            'summary': 'IP: 127.0.0.1/8, 192.168.0.106/32, ::1/128'},
        'mgmt': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': ['127.0.0.1/8',
                                   '::1/128']},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': 'de:ae:4e:ea:6a:0a',
                'members': {},
                'min_links': '',
                'mtu': 65536,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'VRF',
            'speed': 'N/A',
            'summary': 'IP: 127.0.0.1/8, ::1/128'},
        'swp1': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '[an]',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': ['10.0.1.0/31']},
                'ip_neighbors': {
                    'ipv4': ['0c:fe:87:48:02:00'],
                    'ipv6': []},
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:01',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Interface/L3',
            'speed': '1G',
            'summary': 'Master: TestCust1-Prod(UP)\nIP: 10.0.1.0/31'},
        'swp2': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'mac': '0c:33:0e:25:52:02',
                'members': {},
                'min_links': '',
                'mtu': 1500,
                'native_vlan': 100,
                'vlan_filtering': True,
                'vlan_list': "71-72,100"},
            'linkstate': 'UP',
            'mode': 'Access/L2',
            'speed': '1G',
            'summary': 'Master: bridge(UP)'},
        'swp3': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:03',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'BondMember',
            'speed': '1G',
            'summary': 'Master: bond20(UP)'},
        'swp5': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '[an]',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:05',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': 71,
                'vlan_filtering': True,
                'vlan_list': '71'},
            'linkstate': 'UP',
            'mode': 'Access/L2',
            'speed': '1G',
            'summary': 'Master: bridge(UP)'},
        'swp6': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '[an]',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:06',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': 72,
                'vlan_filtering': True,
                'vlan_list': '72'},
            'linkstate': 'UP',
            'mode': 'Access/L2',
            'speed': '1G',
            'summary': 'Master: bridge(UP)'},
        'swp7': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '[anpp]',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': ['192.168.1.15/31']},
                'ip_neighbors': {
                    'ipv4': ['0c:33:0e:eb:6e:08'],
                    'ipv6': ['0c:33:0e:eb:6e:08']},
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:07',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Interface/L3',
            'speed': '1G',
            'summary': 'IP: 192.168.1.15/31'},
        'swp8': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '[anpp]',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': ['192.168.2.15/31']},
                'ip_neighbors': {
                    'ipv4': ['0c:33:0e:01:5d:08'],
                    'ipv6': ['0c:33:0e:01:5d:08']},
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:08',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Interface/L3',
            'speed': '1G',
            'summary': 'IP: 192.168.2.15/31'},
        'swp9': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '[anpp]',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': ['192.168.3.15/31']},
                'ip_neighbors': {
                    'ipv4': ['0c:33:0e:b4:1a:08'],
                    'ipv6': ['0c:33:0e:b4:1a:08']},
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:09',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Interface/L3',
            'speed': '1G',
            'summary': 'IP: 192.168.3.15/31'},
        'vlan100': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '[an]',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:06',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Default',
            'speed': 'N/A',
            'summary': 'Master: vrf-red(UP)'},
        'vlan100-v0': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': ['10.0.0.1/24']},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': 'f2:69:81:6e:3a:3d',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Interface/L3',
            'speed': 'N/A',
            'summary': 'Master: vrf-red(UP)\nIP: 10.0.0.1/24'},
        'vlan250': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '[an]',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:06',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Default',
            'speed': 'N/A',
            'summary': 'Master: green(UP)'},
        'vlan250-v0': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': ['10.0.0.1/24']},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': 'f2:69:81:6e:3a:3d',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Interface/L3',
            'speed': 'N/A',
            'summary': 'Master: green(UP)\nIP: 10.0.0.1/24'},
        'vlan4001': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '[an]',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': ['127.255.0.1/32']},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:06',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Interface/L3',
            'speed': 'N/A',
            'summary': 'Master: green(UP)\nIP: 127.255.0.1/32'},
        'vlan4074': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:06',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Default',
            'speed': 'N/A',
            'summary': 'Master: green(UP)'},
        'vlan4086': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:06',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Default',
            'speed': 'N/A',
            'summary': 'Master: TestCust1-Prod(UP)'},
        'vlan71': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '[an]',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:06',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Default',
            'speed': 'N/A',
            'summary': 'Master: TestCust1-Prod(UP)'},
        'vlan71-v0': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': ['10.0.0.1/24',
                                   '2607:f148:f:71::1/64']},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': 'f2:69:81:6e:3a:3d',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Interface/L3',
            'speed': 'N/A',
            'summary': 'Master: TestCust1-Prod(UP)\n'
                       'IP: 10.0.0.1/24, 2607:f148:f:71::1/64'},
        'vlan72': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '[an]',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': {
                    'ipv4': [],
                    'ipv6': ['0c:fe:87:c6:a3:03']},
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '0c:33:0e:25:52:06',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Default',
            'speed': 'N/A',
            'summary': 'Master: TestCust1-Prod(UP)'},
        'vlan72-v0': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': ['10.1.0.1/24',
                                   '2607:f148:f:72::1/64']},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': 'f2:69:81:6e:3a:3d',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'Interface/L3',
            'speed': 'N/A',
            'summary': 'Master: TestCust1-Prod(UP)\n'
                       'IP: 10.1.0.1/24, 2607:f148:f:72::1/64'},
        'vrf-red': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': 'e6:97:d1:d5:96:35',
                'members': {},
                'min_links': '',
                'mtu': 65536,
                'native_vlan': None,
                'vlan_filtering': False,
                'vlan_list': []},
            'linkstate': 'UP',
            'mode': 'VRF',
            'speed': 'N/A',
            'summary': ''},
        'vxlan111001': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '46:7d:f6:79:4f:75',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': 4074,
                'vlan_filtering': True,
                'vlan_list': '4074'},
            'linkstate': 'UP',
            'mode': 'Access/L2',
            'speed': 'N/A',
            'summary': 'Master: bridge(UP)'},
        'vxlan70000': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': 'ce:dd:93:37:3b:cc',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': 4086,
                'vlan_filtering': True,
                'vlan_list': '4086'},
            'linkstate': 'UP',
            'mode': 'Access/L2',
            'speed': 'N/A',
            'summary': 'Master: bridge(UP)'},
        'vxlan70001': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': '96:87:9f:62:41:c3',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': 71,
                'vlan_filtering': True,
                'vlan_list': '71'},
            'linkstate': 'UP',
            'mode': 'Access/L2',
            'speed': 'N/A',
            'summary': 'Master: bridge(UP)'},
        'vxlan70002': {
            'connector_type': 'Unknown',
            'iface_obj': {
                'description': '',
                'dhcp_enabled': False,
                'ip_address': {
                    'allentries': []},
                'ip_neighbors': None,
                'lacp': {
                    'bypass': '',
                    'partner_mac': '',
                    'rate': '',
                    'sys_priority': ''},
                'mac': 'ca:69:66:52:98:9a',
                'members': {},
                'min_links': '',
                'mtu': 9216,
                'native_vlan': 72,
                'vlan_filtering': True,
                'vlan_list': '72'},
            'linkstate': 'UP',
            'mode': 'Access/L2',
            'speed': 'N/A',
            'summary': 'Master: bridge(UP)'}}


@pytest.fixture
def test_vrf_list():
    return [
        'TestCust1-Prod',
        'connmgmt',
        'green',
        'mgmt',
        'vrf-red'
    ]


@pytest.fixture
def test_vlan_data():
    return {
        'bridge': [
            {'flags': [],
             'vlan': 71,
             'vlanEnd': 72},
            {'vlan': 88},
            {'vlan': 100},
            {'vlan': 250},
            {'vlan': 4001},
            {'vlan': 4074},
            {'vlan': 4086}],
        'swp5': [
            {'flags': ['PVID', 'Egress Untagged'],
             'vlan': 71}],
        'swp6': [
            {'flags': ['PVID', 'Egress Untagged'],
             'vlan': 72}],
        'vxlan111001': [
            {'flags': ['PVID', 'Egress Untagged'],
             'vlan': 4074,
             'vni': 111001}],
        'vxlan70000': [
            {'flags': ['PVID', 'Egress Untagged'],
             'vlan': 4086,
             'vni': 70000}],
        'vxlan70001': [
            {'flags': ['PVID', 'Egress Untagged'],
             'vlan': 71,
             'vni': 70001}],
        'vxlan70002': [
            {'flags': ['PVID', 'Egress Untagged'],
             'vlan': 72,
             'vni': 70002}]}


@pytest.fixture
def test_evpn_vni_data():
    return {
        '70002': {
            'vni': 70002,
            'type': 'L2',
            'vxlanIf': 'vxlan70002',
            'numMacs': 3,
            'numArpNd': 5,
            'numRemoteVteps': 3,
            'tenantVrf': 'TestCust1-Prod',
            'remoteVteps': [
                '192.168.0.101',
                '192.168.0.105',
                '192.168.0.102'
            ]
        },
        '70001': {
            'vni': 70001,
            'type': 'L2',
            'vxlanIf': 'vxlan70001',
            'numMacs': 4,
            'numArpNd': 4,
            'numRemoteVteps': 3,
            'tenantVrf': 'TestCust1-Prod',
            'remoteVteps': [
                '192.168.0.101',
                '192.168.0.16',
                '192.168.0.105'
            ]
        },
        '111001': {
            'vni': 111001,
            'vxlanIf': 'vxlan111001',
            'numMacs': 0,
            'numArpNd': 0,
            'numRemoteVteps': 'n/a',
            'type': 'L3',
            'tenantVrf': 'green'
        },
        '70000': {
            'vni': 70000,
            'vxlanIf': 'vxlan70000',
            'numMacs': 1,
            'numArpNd': 1,
            'numRemoteVteps': 'n/a',
            'type': 'L3',
            'tenantVrf': 'TestCust1-Prod'
        }
    }


@pytest.fixture
def test_bgp_evpn_data():
    return {
        'advertiseGatewayMacip': 'Disabled',
        'advertiseSviMacIp': 'Disabled',
        'advertiseAllVnis': 'Enabled',
        'flooding': 'Head-end replication',
        'numVnis': 4,
        'numL2Vnis': 2,
        'numL3Vnis': 2,
        '70002': {
            'vni': 70002,
            'type': 'L2',
            'inKernel': 'True',
            'rd': '192.168.0.106:2',
            'originatorIp': '192.168.0.106',
            'mcastGroup': '0.0.0.0',
            'advertiseGatewayMacip': 'Disabled',
            'advertiseSviMacIp': 'Disabled',
            'importRTs': [
                '65002:70002'
            ],
            'exportRTs': [
                '65002:70002'
            ]
        },
        '70001': {
            'vni': 70001,
            'type': 'L2',
            'inKernel': 'True',
            'rd': '192.168.0.106:4',
            'originatorIp': '192.168.0.106',
            'mcastGroup': '0.0.0.0',
            'advertiseGatewayMacip': 'Disabled',
            'advertiseSviMacIp': 'Disabled',
            'importRTs': [
                '65002:70001'
            ],
            'exportRTs': [
                '65002:70001'
            ]
        },
        '70000': {
            'vni': 70000,
            'type': 'L3',
            'inKernel': 'True',
            'originatorIp': '192.168.0.106',
            'rd': '192.168.0.106:5',
            'advertiseGatewayMacip': 'n/a',
            'advertiseSviMacIp': 'n/a',
            'advertisePip': 'Enabled',
            'sysIP': '192.168.0.106',
            'sysMAC': '0c:33:0e:25:52:05',
            'rmac': '0c:33:0e:25:52:05',
            'importRTs': [
                '65002:70000'
            ],
            'exportRTs': [
                '65002:70000'
            ]
        },
        '111001': {
            'vni': 111001,
            'type': 'L3',
            'inKernel': 'True',
            'originatorIp': '192.168.0.106',
            'rd': '192.168.0.106:6',
            'advertiseGatewayMacip': 'n/a',
            'advertiseSviMacIp': 'n/a',
            'advertisePip': 'Enabled',
            'sysIP': '192.168.0.106',
            'sysMAC': '0c:33:0e:25:52:05',
            'rmac': '0c:33:0e:25:52:05',
            'importRTs': [
                '65002:111001'
            ],
            'exportRTs': [
                '65002:111001'
            ]
        }
    }


@pytest.fixture
def test_ip_vrf_data():
    return '''12: TestCust1-Prod: <NOARP,MASTER,UP,LOWER_UP> mtu 65536 qdisc noqueue state UP mode DEFAULT group default qlen 1000\    link/ether f2:01:34:39:d1:47 brd ff:ff:ff:ff:ff:ff
24: connmgmt: <NOARP,MASTER,UP,LOWER_UP> mtu 65536 qdisc noqueue state UP mode DEFAULT group default qlen 1000\    link/ether 62:2b:5d:02:2d:ac brd ff:ff:ff:ff:ff:ff
26: green: <NOARP,MASTER,UP,LOWER_UP> mtu 65536 qdisc noqueue state UP mode DEFAULT group default qlen 1000\    link/ether c2:57:63:bd:7e:5b brd ff:ff:ff:ff:ff:ff
30: mgmt: <NOARP,MASTER,UP,LOWER_UP> mtu 65536 qdisc noqueue state UP mode DEFAULT group default qlen 1000\    link/ether de:ae:4e:ea:6a:0a brd ff:ff:ff:ff:ff:ff
32: vrf-red: <NOARP,MASTER,UP,LOWER_UP> mtu 65536 qdisc noqueue state UP mode DEFAULT group default qlen 1000\    link/ether e6:97:d1:d5:96:35 brd ff:ff:ff:ff:ff:ff
'''


@pytest.fixture()
def test_vxlan_data():
    return {
        70000: {'l3_vxlan_vlan': 4086,
                'layer': 3,
                'vxlan': an_vxlan.VXLAN(
                    id=70000, source_address='192.168.0.106', layer=3,
                    import_targets=['65002:70000'],
                    export_targets=['65002:70000'],
                    route_distinguisher='192.168.0.106:5',
                    bound_object_id='TestCust1-Prod'),
                'vxlan_if': 'vxlan70000'},
        70001: {'l3_vxlan_vlan': None,
                'layer': 2,
                'vxlan': an_vxlan.VXLAN(
                    id=70001, source_address='192.168.0.106', layer=2,
                    import_targets=['65002:70001'],
                    export_targets=['65002:70001'],
                    route_distinguisher='192.168.0.106:4',
                    bound_object_id=71),
                'vxlan_if': 'vxlan70001'},
        70002: {'l3_vxlan_vlan': None,
                'layer': 2,
                'vxlan': an_vxlan.VXLAN(
                    id=70002, source_address='192.168.0.106', layer=2,
                    import_targets=['65002:70002'],
                    export_targets=['65002:70002'],
                    route_distinguisher='192.168.0.106:2',
                    bound_object_id=72),
                'vxlan_if': 'vxlan70002'},
        111001: {'l3_vxlan_vlan': 4074,
                 'layer': 3,
                 'vxlan': an_vxlan.VXLAN(
                     id=111001, source_address='192.168.0.106', layer=3,
                     import_targets=['65002:111001'],
                     export_targets=['65002:111001'],
                     route_distinguisher='192.168.0.106:6',
                     bound_object_id='green'),
                 'vxlan_if': 'vxlan111001'}}


@pytest.fixture
def test_show_bonds_data():
    return {
        'bond10': {
            'iface_obj': {
                'members': {
                    'swp10': 'swp10',
                    'swp11': 'swp11'
                }
            }
        },
        'bond20': {
            'iface_obj': {
                'members': {
                    'swp3': 'swp3'
                }
            }
        }
    }


@pytest.fixture
def test_show_evpn_es_data():
    return [
        {
            'esi': '00:be:e9:af:00:3f:60:00:00:00',
            'flags': ['remote'],
            'vteps': [
                {
                    'nexthopId': 268435459,
                    'vtep': '192.168.0.101'
                }
            ]
        },
        {
            'accessPort': 'bond20',
            'esi': '03:be:e9:af:17:3f:60:00:00:0a',
            'flags': ['local', 'remote', 'nonDF'],
            'vteps': [
                {
                    'dfAlgorithm': 'preference',
                    'dfPreference': 32767,
                    'nexthopId': 268435460,
                    'vtep': '192.168.0.105'
                }
            ]
        },
        {
            'accessPort': 'bond10',
            'esi': '03:be:e9:af:17:3f:60:00:00:14',
            'flags': ['local', 'nonDF']
        }
    ]

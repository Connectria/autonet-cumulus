import pytest

from autonet.core.objects import interfaces as an_if

from autonet_cumulus.tasks import interface as if_task


@pytest.mark.parametrize('test_name, expected', [
    ('vlan88', 88),
    ('vlan2', 2),
    ('vlan4042', 4042)
])
def test_parse_svi_name(test_name, expected):
    assert if_task.parse_svi_name(test_name) == expected


@pytest.mark.parametrize('test_speed, expected', [
    ('100M', (100, 'full')),
    ('1G', (1000, 'full')),
    ('10G', (10000, 'full')),
    ('25G', (25000, 'full')),
    ('40G', (40000, 'full')),
    ('50G', (50000, 'full')),
    ('100G', (100000, 'full')),
    ('N/A', (None, None))
])
def test_parse_speed(test_speed, expected):
    assert if_task.parse_speed(test_speed) == expected


@pytest.mark.parametrize('test_summary, expected', [
    ('Master: TestCust1-Prod(UP)', ('TestCust1-Prod', 'UP')),
    ('IP: 127.0.0.1/8, 192.168.0.106/32, ::1/128', (None, None)),
    ('Master: vrf-red(UP)\nIP: 10.0.0.1/24', ('vrf-red', 'UP')),
    ('', (None, None))
])
def test_parse_summary(test_summary, expected):
    assert if_task.parse_summary(test_summary) == expected


def test_parse_vrf_names(test_show_int_data):
    expected = [
        'TestCust1-Prod',
        'connmgmt',
        'green',
        'mgmt',
        'vrf-red'
    ]
    assert if_task.parse_vrf_names(test_show_int_data) == expected


@pytest.mark.parametrize('test_int_data, expected', [
    ('bond20', 'bond'),
    ('swp6', 'interface'),
    ('vlan71', 'vlan'),
    ('lo', 'loopback'),
    ('bridge', 'bridge'),
    ('vxlan70001', 'vxlan'),
    ('green', 'vrf')
], indirect=['test_int_data'])
def test_get_interface_type(test_int_data, expected):
    int_name, int_data, _ = test_int_data
    int_type = if_task.get_interface_type(int_name, int_data)
    assert int_type == expected


@pytest.mark.parametrize('test_summary, expected', [
    ('Master: bond20(UP)', 'bond20'),
    ('Master: appsrv_09(DN)', 'appsrv_09'),
    ('', None)
])
def test_get_interface_master(test_summary, expected):
    assert if_task.get_interface_master(test_summary) == expected

@pytest.mark.parametrize(
    'test_int_name, test_int_type, test_action, expected',
    [
        ('bond20', 'bond', 'add', 'add bond bond20'),
        ('swp6', 'interface', 'add', 'add interface swp6'),
        ('vlan71', 'vlan', 'add', 'add vlan 71'),
        ('lo', 'loopback', 'add', 'add loopback lo'),
        ('bridge', 'bridge', 'add', 'add bridge bridge'),
        ('vxlan70001', 'vxlan', 'add', 'add vxlan vxlan70001'),
        ('green', 'vrf', 'add', 'add vrf green'),
        ('bond20', 'bond', 'del', 'del bond bond20'),
        ('swp6', 'interface', 'del', 'del interface swp6'),
        ('vlan71', 'vlan', 'del', 'del vlan 71'),
        ('lo', 'loopback', 'del', 'del loopback lo'),
        ('bridge', 'bridge', 'del', 'del bridge bridge'),
        ('vxlan70001', 'vxlan', 'del', 'del vxlan vxlan70001'),
        ('green', 'vrf', 'del', 'del vrf green')
    ])
def test_get_base_command(test_int_name, test_int_type, test_action, expected):
    assert if_task.get_base_command(
        test_int_name, test_int_type, test_action) == expected


@pytest.mark.parametrize('test_addresses, test_virtual, test_virtual_type, expected', [
    (['10.0.0.1/24', 'ea0e:a6b2:68d4:7b21::1/64'],
     False, None,
     [
         an_if.InterfaceAddress(
             family='ipv4', address='10.0.0.1/24',
             virtual=False, virtual_type=None),
         an_if.InterfaceAddress(
             family='ipv6', address='ea0e:a6b2:68d4:7b21::1/64',
             virtual=False, virtual_type=None)
     ]),
    (['198.18.0.1/24'],
     True, 'anycast',
     [
         an_if.InterfaceAddress(
             family='ipv4', address='198.18.0.1/24',
             virtual=True, virtual_type='anycast'),
     ]),
    (['ea0e:a6b2:68d4:7b21::1/64'],
     True, 'anycast', [
         an_if.InterfaceAddress(
             family='ipv6', address='ea0e:a6b2:68d4:7b21::1/64',
             virtual=True, virtual_type='anycast'),
     ]),
    (['198.18.0.1/24', 'ea0e:a6b2:68d4:7b21::1/64'],
     True, 'anycast', [
         an_if.InterfaceAddress(
             family='ipv4', address='198.18.0.1/24',
             virtual=True, virtual_type='anycast'),
         an_if.InterfaceAddress(
             family='ipv6', address='ea0e:a6b2:68d4:7b21::1/64',
             virtual=True, virtual_type='anycast'),
     ]),
    (['198.18.0.1/32', '198.19.255.1/32', 'ea0e:a6b2:68d4:7b21::1/128'],
     False, None,
     [
         an_if.InterfaceAddress(
             family='ipv4', address='198.18.0.1/32',
             virtual=False, virtual_type=None),
         an_if.InterfaceAddress(
             family='ipv4', address='198.19.255.1/32',
             virtual=False, virtual_type=None),
         an_if.InterfaceAddress(
             family='ipv6', address='ea0e:a6b2:68d4:7b21::1/128',
             virtual=False, virtual_type=None)
     ])
])
def test_get_interface_addresses(test_addresses, test_virtual,
                                 test_virtual_type, expected):
    addresses = if_task.get_interface_addresses(
        test_addresses, test_virtual, test_virtual_type)
    assert addresses == expected


@pytest.mark.parametrize('test_int_data, expected', [
    ('swp1', an_if.InterfaceRouteAttributes(
        addresses=[an_if.InterfaceAddress(family='ipv4', address='10.0.1.0/31',
                                          virtual=False, virtual_type=None)],
        vrf='TestCust1-Prod')),
    ('swp7', an_if.InterfaceRouteAttributes(
        addresses=[an_if.InterfaceAddress(family='ipv4', address='192.168.1.15/31',
                                          virtual=False, virtual_type=None)],
        vrf=None)),
    ('vlan100', an_if.InterfaceRouteAttributes(
        addresses=[an_if.InterfaceAddress(family='ipv4', address='10.0.0.1/24',
                                          virtual=True, virtual_type='anycast')],
        vrf='vrf-red')),
    ('vlan71', an_if.InterfaceRouteAttributes(
        addresses=[an_if.InterfaceAddress(family='ipv4', address='10.0.0.1/24',
                                          virtual=True, virtual_type='anycast'),
                   an_if.InterfaceAddress(family='ipv6', address='2607:f148:f:71::1/64',
                                          virtual=True, virtual_type='anycast')],
        vrf='TestCust1-Prod'))
], indirect=['test_int_data'])
def test_get_route_attributes(test_int_data, test_vrf_list, expected):
    _, int_data, subint_data = test_int_data
    route_attributes = if_task.get_route_attributes(
        int_data, test_vrf_list, subint_data)
    assert route_attributes == expected


@pytest.mark.parametrize('test_int_data, expected', [
    ('swp2', an_if.InterfaceBridgeAttributes(
        dot1q_enabled=True, dot1q_vids=[71, 72, 100], dot1q_pvid=100)),
    ('swp5', an_if.InterfaceBridgeAttributes(
        dot1q_enabled=True, dot1q_vids=[71], dot1q_pvid=71)),
], indirect=['test_int_data'])
def test_get_bridge_attributes(test_int_data, expected):
    _, int_data, _ = test_int_data
    bridge_attributes = if_task.get_bridge_attributes(int_data)
    assert bridge_attributes == expected


@pytest.mark.parametrize('test_int_data, expected', [
    ('bond20', an_if.Interface(
        name='bond20', mode='routed', description='[an]', virtual=True,
        attributes=an_if.InterfaceRouteAttributes(addresses=[], vrf=None),
        admin_enabled=True, physical_address='0C-33-0E-25-52-03', child=False,
        parent=None, speed=1000, duplex='full', mtu=9216)),
    ('swp1', an_if.Interface(
        name='swp1', mode='routed', description='[an]', virtual=False,
        attributes=an_if.InterfaceRouteAttributes(
            addresses=[
                an_if.InterfaceAddress(
                    family='ipv4', address='10.0.1.0/31',
                    virtual=False, virtual_type=None)],
            vrf='TestCust1-Prod'),
        admin_enabled=True, physical_address='0C-33-0E-25-52-01', child=False,
        parent=None, speed=1000, duplex='full', mtu=9216)),
    ('swp2', an_if.Interface(
        name='swp2', mode='bridged', description='', virtual=False,
        attributes=an_if.InterfaceBridgeAttributes(
            dot1q_enabled=True, dot1q_vids=[71, 72, 100], dot1q_pvid=100),
        admin_enabled=True, physical_address='0C-33-0E-25-52-02', child=False,
        parent=None, speed=1000, duplex='full', mtu=1500)),
    ('vlan72', an_if.Interface(
        name='vlan72', mode='routed', description='[an]', virtual=True,
        attributes=an_if.InterfaceRouteAttributes(
            addresses=[
                an_if.InterfaceAddress(
                    family='ipv4', address='10.1.0.1/24',
                    virtual=True, virtual_type='anycast'),
                an_if.InterfaceAddress(
                    family='ipv6', address='2607:f148:f:72::1/64',
                    virtual=True, virtual_type='anycast')],
            vrf='TestCust1-Prod'),
        admin_enabled=True, physical_address='0C-33-0E-25-52-06', child=False,
        parent=None, speed=None, duplex=None, mtu=9216)
     )
], indirect=['test_int_data'])
def test_get_interface(test_int_data, test_vrf_list, expected):
    int_name, int_data, subint_data = test_int_data
    interface = if_task.get_interface(int_name, int_data,
                                      subint_data, test_vrf_list)
    assert interface == expected


@pytest.mark.parametrize('test_interface_name, expected', [
    ('bond20', [an_if.Interface(
        name='bond20', mode='routed', description='[an]', virtual=True,
        attributes=an_if.InterfaceRouteAttributes(addresses=[], vrf=None),
        admin_enabled=True, physical_address='0C-33-0E-25-52-03', child=False,
        parent=None, speed=1000, duplex='full', mtu=9216)]),
    ('swp1', [an_if.Interface(
        name='swp1', mode='routed', description='[an]', virtual=False,
        attributes=an_if.InterfaceRouteAttributes(
            addresses=[
                an_if.InterfaceAddress(
                    family='ipv4', address='10.0.1.0/31',
                    virtual=False, virtual_type=None)],
            vrf='TestCust1-Prod'),
        admin_enabled=True, physical_address='0C-33-0E-25-52-01', child=False,
        parent=None, speed=1000, duplex='full', mtu=9216)]),
    ('swp88', []),
    (None, [an_if.Interface(
        name='bond20', mode='routed', description='[an]', virtual=True,
        attributes=an_if.InterfaceRouteAttributes(addresses=[], vrf=None),
        admin_enabled=True, physical_address='0C-33-0E-25-52-03',
        child=False, parent=None, speed=1000, duplex='full', mtu=9216),
        an_if.Interface(
            name='swp1', mode='routed', description='[an]', virtual=False,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[
                    an_if.InterfaceAddress(
                        family='ipv4', address='10.0.1.0/31',
                        virtual=False, virtual_type=None)],
                vrf='TestCust1-Prod'),
            admin_enabled=True, physical_address='0C-33-0E-25-52-01',
            child=False, parent=None, speed=1000, duplex='full', mtu=9216),
        an_if.Interface(
            name='swp2', mode='bridged', description='', virtual=False,
            attributes=an_if.InterfaceBridgeAttributes(
                dot1q_enabled=True, dot1q_vids=[71, 72, 100], dot1q_pvid=100),
            admin_enabled=True, physical_address='0C-33-0E-25-52-02',
            child=False, parent=None, speed=1000, duplex='full', mtu=1500),
        an_if.Interface(
            name='swp3', mode='aggregated', description='', virtual=False,
            attributes=None,
            admin_enabled=True, physical_address='0C-33-0E-25-52-03',
            child=False, parent='bond20', speed=1000, duplex='full', mtu=9216),
        an_if.Interface(
            name='swp5', mode='bridged', description='[an]', virtual=False,
            attributes=an_if.InterfaceBridgeAttributes(
                dot1q_enabled=True, dot1q_vids=[71], dot1q_pvid=71),
            admin_enabled=True, physical_address='0C-33-0E-25-52-05',
            child=False, parent=None, speed=1000, duplex='full', mtu=9216),
        an_if.Interface(
            name='swp6', mode='bridged', description='[an]', virtual=False,
            attributes=an_if.InterfaceBridgeAttributes(
                dot1q_enabled=True, dot1q_vids=[72], dot1q_pvid=72),
            admin_enabled=True, physical_address='0C-33-0E-25-52-06',
            child=False, parent=None, speed=1000, duplex='full', mtu=9216),
        an_if.Interface(
            name='swp7', mode='routed', description='[anpp]', virtual=False,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[
                    an_if.InterfaceAddress(
                        family='ipv4', address='192.168.1.15/31',
                        virtual=False, virtual_type=None)],
                vrf=None),
            admin_enabled=True, physical_address='0C-33-0E-25-52-07',
            child=False, parent=None, speed=1000, duplex='full', mtu=9216),
        an_if.Interface(
            name='swp8', mode='routed', description='[anpp]', virtual=False,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[
                    an_if.InterfaceAddress(
                        family='ipv4', address='192.168.2.15/31',
                        virtual=False, virtual_type=None)],
                vrf=None),
            admin_enabled=True, physical_address='0C-33-0E-25-52-08',
            child=False, parent=None, speed=1000, duplex='full', mtu=9216),
        an_if.Interface(
            name='swp9', mode='routed', description='[anpp]', virtual=False,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[
                    an_if.InterfaceAddress(
                        family='ipv4', address='192.168.3.15/31',
                        virtual=False, virtual_type=None)],
                vrf=None),
            admin_enabled=True, physical_address='0C-33-0E-25-52-09',
            child=False, parent=None, speed=1000, duplex='full', mtu=9216),
        an_if.Interface(
            name='vlan100', mode='routed', description='[an]', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[], vrf='vrf-red'),
            admin_enabled=True, physical_address='0C-33-0E-25-52-06',
            child=False, parent=None, speed=None, duplex=None, mtu=9216),
        an_if.Interface(
            name='vlan100-v0', mode='routed', description='', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[
                    an_if.InterfaceAddress(
                        family='ipv4', address='10.0.0.1/24',
                        virtual=False, virtual_type=None)],
                vrf='vrf-red'),
            admin_enabled=True, physical_address='F2-69-81-6E-3A-3D',
            child=False, parent=None, speed=None, duplex=None, mtu=9216),
        an_if.Interface(
            name='vlan250', mode='routed', description='[an]', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[], vrf='green'),
            admin_enabled=True, physical_address='0C-33-0E-25-52-06',
            child=False, parent=None, speed=None, duplex=None, mtu=9216),
        an_if.Interface(
            name='vlan250-v0', mode='routed', description='', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[
                    an_if.InterfaceAddress(
                        family='ipv4', address='10.0.0.1/24',
                        virtual=False, virtual_type=None)],
                vrf='green'),
            admin_enabled=True, physical_address='F2-69-81-6E-3A-3D',
            child=False, parent=None, speed=None, duplex=None, mtu=9216),
        an_if.Interface(
            name='vlan4001', mode='routed', description='[an]', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[
                    an_if.InterfaceAddress(
                        family='ipv4', address='127.255.0.1/32',
                        virtual=False, virtual_type=None)],
                vrf='green'),
            admin_enabled=True, physical_address='0C-33-0E-25-52-06',
            child=False, parent=None, speed=None, duplex=None, mtu=9216),
        an_if.Interface(
            name='vlan4074', mode='routed', description='', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[], vrf='green'),
            admin_enabled=True, physical_address='0C-33-0E-25-52-06',
            child=False, parent=None, speed=None, duplex=None, mtu=9216),
        an_if.Interface(
            name='vlan4086', mode='routed', description='', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[], vrf='TestCust1-Prod'),
            admin_enabled=True, physical_address='0C-33-0E-25-52-06',
            child=False, parent=None, speed=None, duplex=None, mtu=9216),
        an_if.Interface(
            name='vlan71', mode='routed', description='[an]', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[], vrf='TestCust1-Prod'),
            admin_enabled=True, physical_address='0C-33-0E-25-52-06',
            child=False, parent=None, speed=None, duplex=None, mtu=9216),
        an_if.Interface(
            name='vlan71-v0', mode='routed', description='', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[
                    an_if.InterfaceAddress(
                        family='ipv4', address='10.0.0.1/24',
                        virtual=False, virtual_type=None),
                    an_if.InterfaceAddress(
                        family='ipv6', address='2607:f148:f:71::1/64',
                        virtual=False, virtual_type=None)],
                vrf='TestCust1-Prod'),
            admin_enabled=True, physical_address='F2-69-81-6E-3A-3D',
            child=False, parent=None, speed=None, duplex=None, mtu=9216),
        an_if.Interface(
            name='vlan72', mode='routed', description='[an]', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[], vrf='TestCust1-Prod'),
            admin_enabled=True, physical_address='0C-33-0E-25-52-06',
            child=False, parent=None, speed=None, duplex=None, mtu=9216),
        an_if.Interface(
            name='vlan72-v0', mode='routed', description='', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(
                addresses=[
                    an_if.InterfaceAddress(
                        family='ipv4', address='10.1.0.1/24',
                        virtual=False, virtual_type=None),
                    an_if.InterfaceAddress(
                        family='ipv6', address='2607:f148:f:72::1/64',
                        virtual=False, virtual_type=None)],
                vrf='TestCust1-Prod'),
            admin_enabled=True, physical_address='F2-69-81-6E-3A-3D',
            child=False, parent=None, speed=None, duplex=None, mtu=9216)]
     )
])
def test_get_interfaces(test_show_int_data, test_interface_name, expected):
    interfaces = if_task.get_interfaces(test_show_int_data,
                                        test_interface_name)
    assert interfaces == expected


@pytest.mark.parametrize('test_attributes, expected', [
    (an_if.InterfaceBridgeAttributes(
        dot1q_enabled=False, dot1q_pvid=80),
     [
         'del interface swp1 bridge trunk',
         'del interface swp1 bridge pvid',
         'add interface swp1 bridge access 80'
     ]),
    (an_if.InterfaceBridgeAttributes(
        dot1q_enabled=True, dot1q_pvid=80,
        dot1q_vids=[50, 60, 61, 62, 63, 100]),
     [
         'del interface swp1 bridge access',
         'add interface swp1 bridge pvid 80',
         'add interface swp1 bridge trunk vlans 50,60-63,100'
     ])

])
def test_generate_bridge_commands(test_attributes, expected):
    commands = if_task.generate_bridge_commands(
        test_attributes, 'add interface swp1', 'del interface swp1')
    assert commands == expected


@pytest.mark.parametrize('test_interface, expected', [
    (an_if.Interface(name='swp1', admin_enabled=True,
                     mtu=9000, description='test'),
     [
         'add interface swp1',
         'del interface swp1 link down',
         'add interface swp1 mtu 9000',
         'add interface swp1 alias "test"'
     ]),
    (an_if.Interface(name='swp1', admin_enabled=False),
     [
         'add interface swp1',
         'add interface swp1 link down'
     ]),
])
def test_generate_basic_interface_commands(test_interface, expected):
    commands = if_task.generate_basic_interface_commands(
        test_interface, 'add interface swp1', 'del interface swp1')
    assert commands == expected


@pytest.mark.parametrize('test_interface, test_int_type, expected', [
    (an_if.Interface(
        name='vlan50', attributes=an_if.InterfaceRouteAttributes(
            addresses=[
                an_if.InterfaceAddress(address='198.18.0.1/24'),
                an_if.InterfaceAddress(address='ea0e:a6b2:68d4:7b21::1/64')
            ],
            vrf=None),
        description="test in default",
        admin_enabled=True),
     'vlan',
     [
         'add vlan 50',
         'del vlan 50 link down',
         'add vlan 50 alias "test in default"',
         'del vlan 50 ip forward off',
         'add vlan 50 ip address 198.18.0.1/24',
         'add vlan 50 ipv6 address ea0e:a6b2:68d4:7b21::1/64'
     ]),
    (an_if.Interface(
        name='vlan50', attributes=an_if.InterfaceRouteAttributes(
            addresses=[
                an_if.InterfaceAddress(address='198.18.0.254/24'),
                an_if.InterfaceAddress(address='198.18.0.1/24',
                                       virtual=True, virtual_type='anycast'),
                an_if.InterfaceAddress(address='ea0e:a6b2:68d4:7b21::1/64',
                                       virtual=True, virtual_type='anycast')
            ],
            evpn_anycast_mac='20-00-00-AA-BB-CC',
            vrf='green'),
        description="test in green",
        admin_enabled=False),
     'vlan',
     [
         'add vlan 50',
         'add vlan 50 link down',
         'add vlan 50 alias "test in green"',
         'del vlan 50 ip forward off',
         'add vlan 50 vrf green',
         'add vlan 50 ip address 198.18.0.254/24',
         'add vlan 50 ip address-virtual 20:00:00:aa:bb:cc 198.18.0.1/24',
         'add vlan 50 ipv6 address-virtual 20:00:00:aa:bb:cc ea0e:a6b2:68d4:7b21::1/64'
     ]),
])
def test_generate_create_interface_commands(
        test_interface, test_int_type, expected):
    commands = if_task.generate_create_interface_commands(
        test_interface, test_int_type)
    assert commands == expected


@pytest.mark.parametrize(
    'test_interface, test_int_type, test_update, expected', [
        (an_if.Interface(
            name='bond20', mode='routed', description='test', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(addresses=[
                an_if.InterfaceAddress('198.18.0.1/32')
            ], vrf=None),
            admin_enabled=True, speed=1000, duplex='full', mtu=9000),
         'bond', False,
         [
             'del bond bond20',
             'add bond bond20',
             'del bond bond20 link down',
             'add bond bond20 mtu 9000',
             'add bond bond20 alias "test"',
             'add bond bond20 ip address 198.18.0.1/32',
         ]),
        (an_if.Interface(
            name='swp7', mode='bridged', description='test', virtual=True,
            attributes=an_if.InterfaceBridgeAttributes(
                dot1q_enabled=True, dot1q_vids=[5, 6, 7, 8, 9, 10, 55]
            ),
            admin_enabled=False, speed=10000, duplex='full', mtu=1500),
         'interface', False,
         [
             'del interface swp7',
             'add interface swp7',
             'add interface swp7 link down',
             'add interface swp7 mtu 1500',
             'add interface swp7 alias "test"',
             'add interface swp7 link speed 10000',
             'del interface swp7 bridge access',
             'add interface swp7 bridge trunk vlans 5-10,55'
         ]),
        (an_if.Interface(
            name='vlan55', mode='routed', description='test', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(addresses=[
                an_if.InterfaceAddress('198.18.0.1/32')
            ], vrf=None),
            admin_enabled=False, speed=10000, duplex='full', mtu=1500),
         'vlan', True,
         [
             'add vlan 55',
             'add vlan 55 link down',
             'add vlan 55 mtu 1500',
             'add vlan 55 alias "test"',
             'add vlan 55 ip address 198.18.0.1/32'
         ]),
    ])
def test_generate_update_interface_commands(
        test_interface, test_int_type, test_update, expected):
    commands = if_task.generate_update_interface_commands(
        test_interface, test_int_type, test_update)
    assert commands == expected


@pytest.mark.parametrize('test_interface, test_int_type, expected', [
    (an_if.Interface(
        name='vlan50', attributes=an_if.InterfaceRouteAttributes(
            addresses=[
                an_if.InterfaceAddress(address='198.18.0.1/24'),
                an_if.InterfaceAddress(address='ea0e:a6b2:68d4:7b21::1/64')
            ],
            vrf=None),
        description="test in default",
        admin_enabled=True),
     'vlan',
     [
         'add vlan 50',
         'del vlan 50 link down',
         'add vlan 50 alias "test in default"',
         'del vlan 50 ip forward off',
         'add vlan 50 ip address 198.18.0.1/24',
         'add vlan 50 ipv6 address ea0e:a6b2:68d4:7b21::1/64'
     ]),
    (an_if.Interface(
        name='vlan78', attributes=an_if.InterfaceRouteAttributes(
            addresses=[
                an_if.InterfaceAddress(address='198.18.0.254/24'),
                an_if.InterfaceAddress(address='198.18.0.1/24',
                                       virtual=True, virtual_type='anycast'),
                an_if.InterfaceAddress(address='ea0e:a6b2:68d4:7b21::1/64',
                                       virtual=True, virtual_type='anycast')
            ],
            evpn_anycast_mac='20-00-00-AA-BB-CC',
            vrf='green'),
        description="test in green",
        admin_enabled=False),
     'vlan',
     [
         'add vlan 78',
         'add vlan 78 link down',
         'add vlan 78 alias "test in green"',
         'del vlan 78 ip forward off',
         'add vlan 78 vrf green',
         'add vlan 78 ip address 198.18.0.254/24',
         'add vlan 78 ip address-virtual 20:00:00:aa:bb:cc 198.18.0.1/24',
         'add vlan 78 ipv6 address-virtual 20:00:00:aa:bb:cc ea0e:a6b2:68d4:7b21::1/64'
     ]),
    (an_if.Interface(name='swp7',
                     attributes=an_if.InterfaceBridgeAttributes(
                         dot1q_enabled=False, dot1q_pvid=100
                     )),
     'interface',
     [])
])
def test_generate_create_commands(test_interface, test_int_type, expected):
    commands = if_task.generate_create_commands(test_interface, test_int_type)
    assert commands == expected


@pytest.mark.parametrize(
    'test_interface, test_int_type, test_update, expected', [
        (an_if.Interface(
            name='vlan7', mode='routed', description='test', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(addresses=[
                an_if.InterfaceAddress('198.18.0.1/32')
            ], vrf=None),
            admin_enabled=True, speed=1000, duplex='full', mtu=9000),
         'vlan', False,
         [
             'del vlan 7',
             'add vlan 7',
             'del vlan 7 link down',
             'add vlan 7 mtu 9000',
             'add vlan 7 alias "test"',
             'del vlan 7 ip forward off',
             'add vlan 7 ip address 198.18.0.1/32',
         ]),
        (an_if.Interface(
            name='bond20', mode='bridged', description='test', virtual=True,
            attributes=an_if.InterfaceBridgeAttributes(
                dot1q_enabled=True, dot1q_vids=[5, 6, 7, 8, 9, 10, 55]
            ),
            admin_enabled=False, speed=10000, duplex='full', mtu=1500),
         'bond', False,
         [
             'del bond bond20',
             'add bond bond20',
             'add bond bond20 link down',
             'add bond bond20 mtu 1500',
             'add bond bond20 alias "test"',
             'del bond bond20 bridge access',
             'add bond bond20 bridge trunk vlans 5-10,55'
         ]),
        (an_if.Interface(
            name='lo', mode='routed', description='test', virtual=True,
            attributes=an_if.InterfaceRouteAttributes(addresses=[
                an_if.InterfaceAddress('198.18.0.1/32')
            ], vrf=None),
            admin_enabled=True),
         'loopback', False,
         []),
    ])
def test_generate_update_commands(
        test_interface, test_int_type, test_update, expected):
    commands = if_task.generate_update_commands(
        test_interface, test_int_type, test_update)
    assert commands == expected


@pytest.mark.parametrize('test_int_name, test_int_type, expected', [
    ('bond20', 'bond', ['del bond bond20']),
    ('swp6', 'interface', ['del interface swp6']),
    ('vlan71', 'vlan', ['del vlan 71']),
    ('lo', 'loopback', ['del loopback lo']),
    ('bridge', 'bridge', ['del bridge bridge']),
    ('vxlan70001', 'vxlan', ['del vxlan vxlan70001']),
    ('green', 'vrf', ['del vrf green'])
])
def test_generate_delete_commands(test_int_name, test_int_type, expected):
    commands = if_task.generate_delete_commands(test_int_name, test_int_type)
    assert commands == expected

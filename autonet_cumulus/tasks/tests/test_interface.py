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
    int_data, subint_data = test_int_data
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
    int_data, _ = test_int_data
    bridge_attributes = if_task.get_bridge_attributes(int_data)
    assert bridge_attributes == expected


@pytest.mark.parametrize('test_int_name, test_int_data, expected', [
    ('bond20', 'bond20', an_if.Interface(
        name='bond20', mode='routed', description='[an]', virtual=True,
        attributes=an_if.InterfaceRouteAttributes(addresses=[], vrf=None),
        admin_enabled=True, physical_address='0C-33-0E-25-52-03', child=False,
        parent=None, speed=1000, duplex='full', mtu=9216)),
    ('swp1', 'swp1', an_if.Interface(
        name='swp1', mode='routed', description='[an]', virtual=False,
        attributes=an_if.InterfaceRouteAttributes(
            addresses=[
                an_if.InterfaceAddress(
                    family='ipv4', address='10.0.1.0/31',
                    virtual=False, virtual_type=None)],
            vrf='TestCust1-Prod'),
        admin_enabled=True, physical_address='0C-33-0E-25-52-01', child=False,
        parent=None, speed=1000, duplex='full', mtu=9216)),
    ('swp2', 'swp2', an_if.Interface(
        name='swp2', mode='bridged', description='', virtual=False,
        attributes=an_if.InterfaceBridgeAttributes(
            dot1q_enabled=True, dot1q_vids=[71, 72, 100], dot1q_pvid=100),
        admin_enabled=True, physical_address='0C-33-0E-25-52-02', child=False,
        parent=None, speed=1000, duplex='full', mtu=1500)),
    ('vlan72', 'vlan72', an_if.Interface(
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
def test_get_interface(test_int_name, test_int_data, test_vrf_list, expected):
    int_data, subint_data = test_int_data
    interface = if_task.get_interface(test_int_name, int_data,
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
            name='swp3', mode='routed', description='', virtual=False,
            attributes=an_if.InterfaceRouteAttributes(addresses=[], vrf=None),
            admin_enabled=True, physical_address='0C-33-0E-25-52-03',
            child=False, parent=None, speed=1000, duplex='full', mtu=9216),
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


@pytest.mark.parametrize('test_interface, expected', [
    (an_if.Interface(
        name='vlan50', attributes=an_if.InterfaceRouteAttributes(
            addresses=[
                an_if.InterfaceAddress(address='198.18.0.1/24'),
                an_if.InterfaceAddress(address='ea0e:a6b2:68d4:7b21::1/64')
            ],
            vrf=None),
        description="test in default",
        admin_enabled=True),
     [
         'add vlan 50',
         'add vlan 50 ip address 198.18.0.1/24',
         'add vlan 50 ipv6 address ea0e:a6b2:68d4:7b21::1/64',
         'add vlan 50 alias "test in default"'
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
     [
         'add vlan 50',
         'add vlan 50 link down',
         'add vlan 50 vrf green',
         'add vlan 50 ip address 198.18.0.254/24',
         'add vlan 50 ip address-virtual 20:00:00:aa:bb:cc 198.18.0.1/24',
         'add vlan 50 ipv6 address-virtual 20:00:00:aa:bb:cc ea0e:a6b2:68d4:7b21::1/64',
         'add vlan 50 alias "test in green"'
     ]),
])
def test_generate_create_svi_commands(test_interface, expected):
    commands = if_task.generate_create_svi_commands(test_interface)
    assert commands == expected

@pytest.mark.parametrize('test_interface, expected', [
    (an_if.Interface(
        name='vlan50', attributes=an_if.InterfaceRouteAttributes(
            addresses=[
                an_if.InterfaceAddress(address='198.18.0.1/24'),
                an_if.InterfaceAddress(address='ea0e:a6b2:68d4:7b21::1/64')
            ],
            vrf=None),
        description="test in default",
        admin_enabled=True),
     [
         'add vlan 50',
         'add vlan 50 ip address 198.18.0.1/24',
         'add vlan 50 ipv6 address ea0e:a6b2:68d4:7b21::1/64',
         'add vlan 50 alias "test in default"'
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
     [
         'add vlan 50',
         'add vlan 50 link down',
         'add vlan 50 vrf green',
         'add vlan 50 ip address 198.18.0.254/24',
         'add vlan 50 ip address-virtual 20:00:00:aa:bb:cc 198.18.0.1/24',
         'add vlan 50 ipv6 address-virtual 20:00:00:aa:bb:cc ea0e:a6b2:68d4:7b21::1/64',
         'add vlan 50 alias "test in green"'
     ]),
    (an_if.Interface(name='swp7',
                     attributes=an_if.InterfaceBridgeAttributes(
                         dot1q_enabled=False, dot1q_pvid=100
                     )),
     [])
])
def test_generate_create_commands(test_interface, expected):
    commands = if_task.generate_create_commands(test_interface)
    assert commands == expected

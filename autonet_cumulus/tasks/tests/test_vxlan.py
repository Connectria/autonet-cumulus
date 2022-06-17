import pytest

from autonet.core.objects import vxlan as an_vxlan

from autonet_cumulus.tasks import vxlan as vxlan_task


def test_parse_vxlan_data(test_evpn_vni_data, test_bgp_evpn_data,
                          test_vlan_data, test_vxlan_data):
    vxlan_data = vxlan_task.parse_vxlan_data(
        test_evpn_vni_data, test_bgp_evpn_data, test_vlan_data)
    assert vxlan_data == test_vxlan_data


@pytest.mark.parametrize('test_vnid, expected', [
    ('70001', [
        an_vxlan.VXLAN(
            id=70001, source_address='192.168.0.106', layer=2,
            import_targets=['65002:70001'],
            export_targets=['65002:70001'],
            route_distinguisher='192.168.0.106:4',
            bound_object_id=71)]
     ),
    ('111001', [
        an_vxlan.VXLAN(
            id=111001, source_address='192.168.0.106', layer=3,
            import_targets=['65002:111001'],
            export_targets=['65002:111001'],
            route_distinguisher='192.168.0.106:6',
            bound_object_id='green')
    ]),
    (None, [
        an_vxlan.VXLAN(id=70000, source_address='192.168.0.106', layer=3,
                       import_targets=['65002:70000'],
                       export_targets=['65002:70000'],
                       route_distinguisher='192.168.0.106:5',
                       bound_object_id='TestCust1-Prod'),
        an_vxlan.VXLAN(id=70001, source_address='192.168.0.106', layer=2,
                       import_targets=['65002:70001'],
                       export_targets=['65002:70001'],
                       route_distinguisher='192.168.0.106:4',
                       bound_object_id=71),
        an_vxlan.VXLAN(id=70002, source_address='192.168.0.106', layer=2,
                       import_targets=['65002:70002'],
                       export_targets=['65002:70002'],
                       route_distinguisher='192.168.0.106:2',
                       bound_object_id=72),
        an_vxlan.VXLAN(id=111001, source_address='192.168.0.106', layer=3,
                       import_targets=['65002:111001'],
                       export_targets=['65002:111001'],
                       route_distinguisher='192.168.0.106:6',
                       bound_object_id='green')
    ])
])
def test_get_vxlans(test_vxlan_data, test_vnid, expected):
    assert vxlan_task.get_vxlans(test_vxlan_data, test_vnid) == expected


@pytest.mark.parametrize('test_vxlan, expected', [
    (an_vxlan.VXLAN(id=155115, source_address='198.18.0.55', layer=3,
                    import_targets=['65000:5', 'auto'],
                    export_targets=['65000:5'],
                    route_distinguisher='auto',
                    bound_object_id='green'),
     ['add bgp vrf green evpn route-target import 65000:5',
      'add bgp vrf green evpn route-target import 65155:155115',
      'add bgp vrf green evpn route-target export 65000:5']),
    (an_vxlan.VXLAN(id=70005, source_address='198.18.0.55', layer=2,
                    import_targets=['auto'],
                    export_targets=['65155:70001', '65155:5'],
                    route_distinguisher='198.18.0.55:5',
                    bound_object_id=5),
     ['add bgp l2vpn evpn vni 70005 route-target import 65155:70005',
      'add bgp l2vpn evpn vni 70005 route-target export 65155:70001',
      'add bgp l2vpn evpn vni 70005 route-target export 65155:5']),
])
def test_generate_vxlan_rt_commands(test_vxlan, expected):
    commands = vxlan_task.generate_vxlan_rt_commands(test_vxlan, '65155')
    assert commands == expected


@pytest.mark.parametrize(
    'test_vxlan, test_bgp_data, test_ip_forward, expected', [
        (an_vxlan.VXLAN(id=70005, source_address='198.18.0.55', layer=2,
                        import_targets=['auto'],
                        export_targets=['65155:70001', '65155:5'],
                        route_distinguisher='198.18.0.55:5',
                        bound_object_id=5),
         {'asn': 65155, 'rid': '198.18.0.55'}, False,
         [
             'add vxlan vxlan70005 bridge access 5',
             'add bgp l2vpn evpn vni 70005 rd 198.18.0.55:5',
             'add vlan 5 ip forward off',
         ]),
        (an_vxlan.VXLAN(id=191871, source_address='198.18.8.92', layer=2,
                        import_targets=['auto'],
                        export_targets=['auto'],
                        route_distinguisher='auto',
                        bound_object_id=1871),
         {'asn': 65005, 'rid': '198.18.8.92'}, True,
         [
             'add vxlan vxlan191871 bridge access 1871',
             'add bgp l2vpn evpn vni 191871 rd 198.18.8.92:1871'
         ])
    ])
def test_generate_create_l2_vxlan_commands(test_vxlan, test_bgp_data,
                                           test_ip_forward, expected):
    commands = vxlan_task.generate_create_l2_vxlan_commands(
        test_vxlan, test_bgp_data, test_ip_forward)
    assert commands == expected


@pytest.mark.parametrize('test_vxlan, test_bgp_data, test_dynamic_vlan, expected', [
    (an_vxlan.VXLAN(id=70005, source_address='198.18.0.55', layer=3,
                    import_targets=['auto'],
                    export_targets=['65155:70001', '65155:5'],
                    route_distinguisher='198.18.0.55:5',
                    bound_object_id="green"),
     {'asn': 65155, 'rid': '198.18.0.55'}, 4094,
     [
         'add vxlan vxlan70005 bridge access 4094',
         'add vlan 4094 vrf green',
         'add bgp vrf green autonomous-system 65155',
         'add bgp vrf green ipv4 unicast redistribute connected',
         'add bgp vrf green ipv4 unicast redistribute static',
         'add bgp vrf green ipv6 unicast redistribute connected',
         'add bgp vrf green ipv6 unicast redistribute static',
         'add bgp vrf green l2vpn evpn advertise ipv4 unicast',
         'add bgp vrf green l2vpn evpn advertise ipv6 unicast',
         'add vrf green vni 70005'
     ]),
    (an_vxlan.VXLAN(id=191871, source_address='198.18.8.92', layer=3,
                    import_targets=['auto'],
                    export_targets=['auto'],
                    route_distinguisher='auto',
                    bound_object_id="taupe"),
     {'asn': 65005, 'rid': '198.18.8.92'}, 250,
     [
         'add vxlan vxlan191871 bridge access 250',
         'add vlan 250 vrf taupe',
         'add bgp vrf taupe autonomous-system 65005',
         'add bgp vrf taupe ipv4 unicast redistribute connected',
         'add bgp vrf taupe ipv4 unicast redistribute static',
         'add bgp vrf taupe ipv6 unicast redistribute connected',
         'add bgp vrf taupe ipv6 unicast redistribute static',
         'add bgp vrf taupe l2vpn evpn advertise ipv4 unicast',
         'add bgp vrf taupe l2vpn evpn advertise ipv6 unicast',
         'add vrf taupe vni 191871'
     ])
])
def test_generate_create_l3_vxlan_commands(test_vxlan, test_bgp_data,
                                           test_dynamic_vlan, expected):
    commands = vxlan_task.generate_create_l3_vxlan_commands(
        test_vxlan, test_bgp_data, test_dynamic_vlan)
    assert commands == expected


@pytest.mark.parametrize(
    'test_vxlan, test_bgp_data, test_dynamic_vlan, expected',
    [
        (an_vxlan.VXLAN(id=70005, source_address='198.18.0.55', layer=3,
                        import_targets=['auto'],
                        export_targets=['65155:70001', '65155:5'],
                        route_distinguisher='198.18.0.55:5',
                        bound_object_id="green"),
         {'asn': 65155, 'rid': '198.18.0.55'}, 4095,
         [
             'add vxlan vxlan70005 vxlan id 70005',
             'add vxlan vxlan70005 vxlan local-tunnelip 198.18.0.55',
             'add vxlan vxlan70005 bridge learning off',
             'add vxlan vxlan70005 bridge arp-nd-suppress on',
             'add vxlan vxlan70005 bridge access 4095',
             'add vlan 4095 vrf green',
             'add bgp vrf green autonomous-system 65155',
             'add bgp vrf green ipv4 unicast redistribute connected',
             'add bgp vrf green ipv4 unicast redistribute static',
             'add bgp vrf green ipv6 unicast redistribute connected',
             'add bgp vrf green ipv6 unicast redistribute static',
             'add bgp vrf green l2vpn evpn advertise ipv4 unicast',
             'add bgp vrf green l2vpn evpn advertise ipv6 unicast',
             'add vrf green vni 70005',
             'add bgp vrf green evpn route-target import 65155:70005',
             'add bgp vrf green evpn route-target export 65155:70001',
             'add bgp vrf green evpn route-target export 65155:5'
         ]),
        (an_vxlan.VXLAN(id=191871, source_address='198.18.8.92', layer=3,
                        import_targets=['auto'],
                        export_targets=['auto'],
                        route_distinguisher='auto',
                        bound_object_id="taupe"),
         {'asn': 65005, 'rid': '198.18.8.92'}, 250,
         [
             'add vxlan vxlan191871 vxlan id 191871',
             'add vxlan vxlan191871 vxlan local-tunnelip 198.18.8.92',
             'add vxlan vxlan191871 bridge learning off',
             'add vxlan vxlan191871 bridge arp-nd-suppress on',
             'add vxlan vxlan191871 bridge access 250',
             'add vlan 250 vrf taupe',
             'add bgp vrf taupe autonomous-system 65005',
             'add bgp vrf taupe ipv4 unicast redistribute connected',
             'add bgp vrf taupe ipv4 unicast redistribute static',
             'add bgp vrf taupe ipv6 unicast redistribute connected',
             'add bgp vrf taupe ipv6 unicast redistribute static',
             'add bgp vrf taupe l2vpn evpn advertise ipv4 unicast',
             'add bgp vrf taupe l2vpn evpn advertise ipv6 unicast',
             'add vrf taupe vni 191871',
             'add bgp vrf taupe evpn route-target import 65005:191871',
             'add bgp vrf taupe evpn route-target export 65005:191871'
         ]),
        (an_vxlan.VXLAN(id=70005, source_address='198.18.0.55', layer=2,
                        import_targets=['auto'],
                        export_targets=['65155:70001', '65155:5'],
                        route_distinguisher='198.18.0.55:5',
                        bound_object_id=5),
         {'asn': 65155, 'rid': '198.18.0.55'}, None,
         [
             'add vxlan vxlan70005 vxlan id 70005',
             'add vxlan vxlan70005 vxlan local-tunnelip 198.18.0.55',
             'add vxlan vxlan70005 bridge learning off',
             'add vxlan vxlan70005 bridge arp-nd-suppress on',
             'add vxlan vxlan70005 bridge access 5',
             'add bgp l2vpn evpn vni 70005 rd 198.18.0.55:5',
             'add vlan 5 ip forward off',
             'add bgp l2vpn evpn vni 70005 route-target import 65155:70005',
             'add bgp l2vpn evpn vni 70005 route-target export 65155:70001',
             'add bgp l2vpn evpn vni 70005 route-target export 65155:5'
         ]),
        (an_vxlan.VXLAN(id=191871, source_address='198.18.8.92', layer=2,
                        import_targets=['auto'],
                        export_targets=['auto'],
                        route_distinguisher='auto',
                        bound_object_id=1871),
         {'asn': 65005, 'rid': '198.18.8.92'}, None,
         [
             'add vxlan vxlan191871 vxlan id 191871',
             'add vxlan vxlan191871 vxlan local-tunnelip 198.18.8.92',
             'add vxlan vxlan191871 bridge learning off',
             'add vxlan vxlan191871 bridge arp-nd-suppress on',
             'add vxlan vxlan191871 bridge access 1871',
             'add bgp l2vpn evpn vni 191871 rd 198.18.8.92:1871',
             'add vlan 1871 ip forward off',
             'add bgp l2vpn evpn vni 191871 route-target import 65005:191871',
             'add bgp l2vpn evpn vni 191871 route-target export 65005:191871'
         ])
    ])
def test_generate_create_vxlan_commands(test_vxlan, test_bgp_data,
                                        test_dynamic_vlan, expected):
    commands = vxlan_task.generate_create_vxlan_commands(
        test_vxlan, test_bgp_data['rid'], test_bgp_data, test_dynamic_vlan)
    assert commands == expected

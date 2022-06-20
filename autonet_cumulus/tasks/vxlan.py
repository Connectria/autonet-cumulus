from autonet.core.objects import vxlan as an_vxlan
from typing import Optional, Union


def parse_vxlan_data(evpn_vni_data: dict, bgp_vni_data: dict,
                     vlan_data: dict) -> dict:
    """
    Cumulus does not have a single source of information for vxlan
    configuration as modeled by Autonet.  Instead, the information
    must be parsed from several command outputs.  This function
    performs that parsing and emits a dictionary of objects indexed
    by VNI that contains a :py:class:`VXLAN` dataclass as well as
    additional metadata that can be used for driver operations.

    :param evpn_vni_data: Output from the :code:`show evpn vni`
        command.
    :param bgp_vni_data: Output from the :code:`show bgp evpn vni`
        command.
    :param vlan_data: Output from the :code:`show bridge vlan`
        command.
    :return:
    """
    vxlan_data = {}
    for evpn_vni, evpn_vni_datum in evpn_vni_data.items():
        if evpn_vni_datum['type'] == 'L2':
            layer = 2
            bound_object_id = vlan_data[evpn_vni_datum['vxlanIf']][0]['vlan']
            l3_vxlan_vlan = None
        elif evpn_vni_datum['type'] == 'L3':
            layer = 3
            bound_object_id = evpn_vni_datum['tenantVrf']
            l3_vxlan_vlan = vlan_data[evpn_vni_datum['vxlanIf']][0]['vlan']
        else:
            # Maybe not fully configured?
            continue
        vxlan_data[int(evpn_vni)] = {
            "layer": layer,
            "vxlan_if": evpn_vni_datum['vxlanIf'],
            "l3_vxlan_vlan": l3_vxlan_vlan,
            "vxlan": an_vxlan.VXLAN(
                id=int(evpn_vni),
                layer=layer,
                source_address=bgp_vni_data[evpn_vni]['originatorIp'],
                bound_object_id=bound_object_id,
                route_distinguisher=bgp_vni_data[evpn_vni]['rd'],
                import_targets=bgp_vni_data[evpn_vni]['importRTs'],
                export_targets=bgp_vni_data[evpn_vni]['exportRTs']
            )
        }
    return vxlan_data


def get_vxlans(vxlan_data: dict,
               vnid: Optional[Union[str, int]]) -> [an_vxlan.VXLAN]:
    """
    Returns a list of configured VXLAN tunnels on the device.

    :param vxlan_data: Dictionary returned by
        :py:meth:`parse_vxlan_data`.
    :param vnid: Filter for the given VNID.
    :return:
    """
    if vnid:
        if int(vnid) in vxlan_data:
            return [vxlan_data[int(vnid)]['vxlan']]
        else:
            return []
    else:
        return [x['vxlan'] for _, x in vxlan_data.items()]


def generate_vxlan_rt_commands(vxlan: an_vxlan.VXLAN, bgp_asn: Union[str, int]) -> [str]:
    """
    Generate a list of RT configuration commands for EVPN import and
    export.

    :param vxlan: A :py:class:`VXLAN` object.
    :param bgp_asn: The BGP ASN to use when generating auto targets.
    :return:
    """
    auto_rt = f'{bgp_asn}:{vxlan.id}'
    l2_template = 'add bgp l2vpn evpn vni {oid} route-target {dir} {rt}'
    l3_template = 'add bgp vrf {oid} evpn route-target {dir} {rt}'
    commands = []
    for direction, rts in {'import': vxlan.import_targets,
                           'export': vxlan.export_targets}.items():
        for rt in rts:
            oid = vxlan.bound_object_id if vxlan.layer == 3 else vxlan.id
            template = l3_template if vxlan.layer == 3 else l2_template
            rt = auto_rt if rt == 'auto' else rt
            commands.append(template.format(oid=oid, dir=direction, rt=rt))

    return commands


def generate_create_l2_vxlan_commands(vxlan: an_vxlan.VXLAN, bgp_data: dict,
                                      ip_forward: bool = False) -> [str]:
    """
    Generate the commands required to set up an L2 VXLAN binding.

    :param vxlan: A :py:class:`VXLAN` object.
    :param bgp_data: BGP data dictionary containing ASN and router ID.
    :param ip_forward: If False then disable ip_forwarding on an SVI
        for a bound vlan.
    :return:
    """
    if vxlan.route_distinguisher == 'auto':
        vxlan.route_distinguisher = f'{bgp_data["rid"]}:{vxlan.bound_object_id}'
    commands = [
        f'add vxlan vxlan{vxlan.id} bridge access {vxlan.bound_object_id}',
        f'add bgp l2vpn evpn vni {vxlan.id} rd {vxlan.route_distinguisher}'
    ]
    if not ip_forward:
        commands.append(f'add vlan {vxlan.bound_object_id} ip forward off', )
    return commands


def generate_create_l3_vxlan_commands(vxlan: an_vxlan.VXLAN, bgp_data: dict,
                                      dynamic_vlan: Optional[int] = None) -> [str]:
    """
    Generate the commands required to set up an L3 VXLAN binding.

    :param vxlan: A :py:class:`VXLAN` object.
    :param bgp_data: BGP data dictionary containing ASN and router ID.
    :param dynamic_vlan: A dynamically assigned VLAN to be used when
        binding an L3 VNI.
    :return:
    """
    if vxlan.route_distinguisher == 'auto':
        vxlan.route_distinguisher = f'{bgp_data["rid"]}:{dynamic_vlan}'
    return [
        f'add vxlan vxlan{vxlan.id} bridge access {dynamic_vlan}',
        f'add vlan {dynamic_vlan} vrf {vxlan.bound_object_id}',
        f'add bgp vrf {vxlan.bound_object_id} autonomous-system {bgp_data["asn"]}',
        f'add bgp vrf {vxlan.bound_object_id} ipv4 unicast redistribute connected',
        f'add bgp vrf {vxlan.bound_object_id} ipv4 unicast redistribute static',
        f'add bgp vrf {vxlan.bound_object_id} ipv6 unicast redistribute connected',
        f'add bgp vrf {vxlan.bound_object_id} ipv6 unicast redistribute static',
        f'add bgp vrf {vxlan.bound_object_id} l2vpn evpn advertise ipv4 unicast',
        f'add bgp vrf {vxlan.bound_object_id} l2vpn evpn advertise ipv6 unicast',
        f'add vrf {vxlan.bound_object_id} vni {vxlan.id}',
    ]


def generate_create_vxlan_commands(
        vxlan: an_vxlan.VXLAN, auto_source: str, bgp_data: dict,
        dynamic_vlan: Optional[int] = None, ip_forward: bool = False) -> [str]:
    """
    Generate a list of commands required to create a VXLAN.

    :param vxlan: A :py:class:`VXLAN` object.
    :param auto_source: The IP address to use when source is set to
        "auto".
    :param bgp_data: BGP data dictionary containing ASN and router ID.
    :param dynamic_vlan: A dynamically assigned VLAN to be used when
        binding an L3 VNI.
    :param ip_forward: If False then disable ip_forwarding on an SVI
        for a bound vlan.
    :return:
    """
    if vxlan.source_address == 'auto':
        vxlan.source_address = auto_source
    commands = [
        f'add vxlan vxlan{vxlan.id} vxlan id {vxlan.id}',
        f'add vxlan vxlan{vxlan.id} vxlan local-tunnelip {vxlan.source_address}',
        f'add vxlan vxlan{vxlan.id} bridge learning off',
        f'add vxlan vxlan{vxlan.id} bridge arp-nd-suppress on',
    ]
    if vxlan.layer == 2:
        commands += generate_create_l2_vxlan_commands(vxlan, bgp_data,
                                                      ip_forward)
    if vxlan.layer == 3:
        commands += generate_create_l3_vxlan_commands(vxlan, bgp_data,
                                                      dynamic_vlan)

    commands += generate_vxlan_rt_commands(vxlan, bgp_data['asn'])
    return commands


def generate_delete_l2_vxlan_commands(vxlan_datum: dict) -> [str]:
    """
    Generate a list of commands required to tear down an L2 VXLAN
    tunnel.

    :param vxlan_datum: The individual vxlan_data object from
        :py:func:`parse_vxlan_data` that represents the VXLAN tunnel.
    :return:
    """
    vni = vxlan_datum['vxlan'].id
    vxlan_if = vxlan_datum["vxlan_if"]
    return [
        f'del bgp l2vpn evpn vni {vni}',
        f'del vxlan {vxlan_if}'
    ]


def generate_delete_l3_vxlan_commands(vxlan_datum: dict) -> [str]:
    """
    Generate a list of commands required to tear down an L3 VXLAN
    tunnel.

    :param vxlan_datum: The individual vxlan_data object from
        :py:func:`parse_vxlan_data` that represents the VXLAN tunnel.
    :return:
    """
    # Setup some vars for easier to read code below.
    vrf = vxlan_datum['vxlan'].bound_object_id
    vni = vxlan_datum['vxlan'].id
    vxlan_if = vxlan_datum["vxlan_if"]
    rd = vxlan_datum['vxlan'].route_distinguisher
    # Destroy basic BGP configuration.
    commands = [
        f'del bgp vrf {vrf} l2vpn evpn vni {vni}',
        f'del bgp vrf {vrf} l2vpn evpn advertise ipv4 unicast',
        f'del bgp vrf {vrf} l2vpn evpn advertise ipv6 unicast',
        f'del bgp vrf {vrf} l2vpn evpn rd {rd}',
    ]
    # Clean up RTs.
    for rt_dir in ['import', 'export']:
        for rt in getattr(vxlan_datum['vxlan'], f'{rt_dir}_targets'):
            commands.append(
                f'del bgp vrf {vrf} l2vpn evpn route-target {rt_dir} {rt}')
    # Clean up VXLAN interface and dynamically bound VLAN.
    commands += [
        f'del vxlan {vxlan_if}',
        f'del vlan {vxlan_datum["l3_vxlan_vlan"]}'
    ]
    return commands


def generate_delete_vxlan_commands(vxlan_id: Union[str, int], vxlan_data: dict):
    """
    Return a list of commands required to tear down a VXLAN tunnel.

    :param vxlan_id: The VNI of the target VXLAN tunnel.
    :param vxlan_data: The output :py:func:`parse_vxlan_data`.
    :return:
    """
    vxlan_datum = vxlan_data[int(vxlan_id)]
    if vxlan_datum['layer'] == 2:
        return generate_delete_l2_vxlan_commands(vxlan_datum)
    if vxlan_datum['layer'] == 3:
        return generate_delete_l3_vxlan_commands(vxlan_datum)

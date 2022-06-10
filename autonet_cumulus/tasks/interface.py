import ipaddress
import re

from autonet.core.objects import interfaces as an_if
from autonet.util.config_string import vlan_list_to_glob, glob_to_vlan_list
from typing import Optional, Tuple, Union

from autonet_cumulus.commands import CommandResultSet, Commands


def parse_svi_name(name: str) -> int:
    """
    Returns the VLAN ID portion of the SVI name.

    :param name: The SVI interface name.
    :return:
    """
    return int(name.lstrip('vlan'))


def parse_speed(speed: str) -> Union[Tuple[int, str], Tuple[None, None]]:
    if speed.endswith('G'):
        return int(speed.strip('G')) * 1000, 'full'
    if speed.endswith('M'):
        return int(speed.strip('M')), 'full'
    return None, None


def parse_summary(summary: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses the summary string from an interface and returns
    a tuple that represents the master interface and its state or
    :code:`None, None`, if there is no master interface.
    :param summary:
    :return:
    """
    regex = r"(Master: (?P<int_name>[\d\w-]*)\((?P<state>[\w]*)\))?"
    matches = re.search(regex, summary)
    return matches.group('int_name'), matches.group('state')


def parse_vrf_names(show_int_data: dict) -> [str]:
    """
    Parses the data from the :code:`show interface` command and returns
    a list of vrf names present.

    :param show_int_data: The data returned from :code:`show interface`
    :return:
    """
    return [name
            for name, data in show_int_data.items()
            if data['mode'] == 'VRF']


def get_interface_addresses(
        addresses: [str], virtual: bool = False, virtual_type: Optional[str] = None
) -> [an_if.InterfaceAddress]:
    """
    Parses a list of CIDR notated addresses into a list of
    :py:class`InterfaceAddress` objects.

    :param addresses:
    :param virtual:
    :param virtual_type:
    :return:
    """
    interface_addresses = []
    for address in addresses:
        ip_interface = ipaddress.ip_interface(address)
        interface_addresses.append(an_if.InterfaceAddress(
            address=ip_interface.with_prefixlen,
            family=f"ipv{ip_interface.version}",
            virtual=virtual,
            virtual_type=virtual_type
        ))
    return interface_addresses


def get_route_attributes(
        int_data: dict, vrf_list: [str], subint_data: dict = None
) -> an_if.InterfaceRouteAttributes:
    """
    Parses the interface data and builds a
    :py:class:`InterfaceRouteAttributes` object.  In the case of an SVI
    with an EVPN anycast gateway the `-v0` interface's data can be
    passed via the :py:attr:`subint_data` argument.
    :param int_data: The interface data from `show interface`.
    :param vrf_list: A list of VRF names.
    :param subint_data: The interface data that corresponds to the data
        passed to the :py:attr:`int_data` argument.
    :return:
    """
    master, _ = parse_summary(int_data['summary'])
    vrf = master if master and master in vrf_list else None

    # parse out standard addresses.
    addresses = get_interface_addresses(
        int_data['iface_obj']['ip_address']['allentries'],
        virtual=False, virtual_type=None
    )
    # parse out EVPN anycast addresses and append them to the list.
    if subint_data:
        addresses += get_interface_addresses(
            subint_data['iface_obj']['ip_address']['allentries'],
            virtual=True, virtual_type='anycast'
        )

    return an_if.InterfaceRouteAttributes(
        addresses=addresses, vrf=vrf
    )


def get_bridge_attributes(int_data: dict) -> an_if.InterfaceBridgeAttributes:
    """
    Parses the interface data and builds a
    :py:class:`InterfaceBridgeAttributes` object.
    :param int_data: The interface data from :code:`show interface`.
    :return:
    """
    return an_if.InterfaceBridgeAttributes(
        dot1q_enabled=int_data['iface_obj']['vlan_filtering'],
        dot1q_pvid=int_data['iface_obj']['native_vlan'],
        dot1q_vids=glob_to_vlan_list(int_data['iface_obj']['vlan_list'])
    )


def get_interface(int_name: str, int_data: dict, subint_data: dict = None,
                  vrf_list: [str] = None) -> an_if.Interface:
    """
    Parses the interface name and data and returns a populated
    :py:class:`Interface` object.  In the case of SVIs, the optional
    :py:attr:`subint_data` would be used to pass in the
    interface data for the `-v0` subinterface that is used for EVPN
    anycast gateways.

    :param int_name: The interface name.
    :param int_data: The interface data from :code:`show interface`.
    :param subint_data: The interface data that corresponds to the data
        passed to the :py:attr:`int_data` argument.
    :param vrf_list: A list of VRF names.
    :return:
    """
    # Determine mode and generate appropriate attributes.
    if int_data['iface_obj']['vlan_list']:
        mode = 'bridged'
        attributes = get_bridge_attributes(int_data)
    else:
        mode = 'routed'
        attributes = get_route_attributes(int_data, vrf_list, subint_data)

    # Determine Speed and Duplex.
    speed, duplex = parse_speed(int_data['speed'])

    return an_if.Interface(
        name=int_name,
        mode=mode,
        description=int_data['iface_obj']['description'],
        attributes=attributes,
        admin_enabled=False if int_data['linkstate'] == 'ADMDN' else True,
        virtual=not int_name.startswith('swp'),
        physical_address=int_data['iface_obj']['mac'],
        duplex=duplex,
        speed=speed,
        parent=None,
        child=False,
        mtu=int_data['iface_obj']['mtu']
    )


def get_interfaces(show_int_data: dict, int_name: str = None) -> [an_if.Interface]:
    """
    Parses the results of several commands to generate a complete list
    of :py:class:`Interface` objects.  If :py:attr:`interface_name` is
    provided then only one :py:class:`Interface` object is returned.

    :param show_int_data: Data from the :code:`show interface` command.
    :param int_name: Filter results to only include the provided
        interface.
    """
    interfaces = []
    vrf_list = parse_vrf_names(show_int_data)

    for cur_int_name, int_data in show_int_data.items():
        # If a specific interface is requested we'll short circuit
        # until we find it.
        if int_name and int_name != cur_int_name:
            continue
        if cur_int_name.startswith('swp'):
            interfaces.append(
                get_interface(cur_int_name, int_data, None, vrf_list))
        if cur_int_name.startswith('vlan'):
            subint_name = f"{int_name}-v0"
            if subint_name in show_int_data:
                subint_data = show_int_data[subint_name]
            else:
                subint_data = None
            interfaces.append(
                get_interface(cur_int_name, int_data, subint_data, vrf_list)
            )
        if 'mode' in int_data and int_data['mode'] == '802.3ad':
            interfaces.append(get_interface(cur_int_name, int_data))

    return interfaces


def generate_create_svi_commands(interface: an_if.Interface) -> [str]:
    """
    Generate a list of commands required to create an SVI.

    :param interface: An :py:class:`Interface` object.
    :return:
    """
    vlan_id = parse_svi_name(interface.name)
    prefix = f'add vlan {vlan_id}'
    commands = [prefix]
    if not interface.admin_enabled:
        commands.append(f'{prefix} link down')
    attributes: an_if.InterfaceRouteAttributes = interface.attributes
    if attributes.vrf:
        commands.append(f'{prefix} vrf {attributes.vrf}')
    for address in attributes.addresses:
        af = 'ip' if address.family == 'ipv4' else 'ipv6'
        if address.virtual and address.virtual_type == 'anycast':
            address_type = 'address-virtual'
            mac = f"{attributes.evpn_anycast_mac} ".lower().replace('-', ':')
        else:
            address_type = 'address'
            mac = ''
        commands.append(f'{prefix} {af} {address_type} {mac}{address.address}')
    if interface.mtu:
        commands.append(f'{prefix} mtu {interface.mtu}')
    if interface.description:
        commands.append(f'{prefix} alias "{interface.description}"')

    return commands


def generate_create_commands(interface: an_if.Interface) -> [str]:
    """
    Generate a list of commands required to create an interface.

    :param interface: An :py:class:`Interface` object.
    :return:
    """
    # Currently, we only support creating SVIs.  We have this logic
    # fork here in anticipation of supporting other types later on.
    if interface.name.startswith('vlan'):
        return generate_create_svi_commands(interface)

    return []

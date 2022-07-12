import ipaddress
import re

from autonet.core.objects import interfaces as an_if
from autonet.util.config_string import vlan_list_to_glob, glob_to_vlan_list
from typing import Optional, Tuple, Union


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


def get_interface_type(int_name, int_data):
    """
    Determine the type of interface represented by the interface name
    or in the case of some many virtual interface types, the interface
    data object.  Command will return a string value that can be used
    in the NETd command string.  If the interface data indicates the
    interface does not exist at all, then None is returned.

    :param int_name: The interface name.
    :param int_data: The interface data object.
    :return:
    """
    if int_name.startswith('swp'):
        return 'interface'
    if int_name.startswith('vlan'):
        return 'vlan'
    if int_data['mode'] == '802.3ad':
        return 'bond'
    if int_data['mode'] == 'VRF':
        return 'vrf'
    if int_data['mode'] == 'Loopback':
        return 'loopback'
    if int_data['mode'] == 'Bridge/L2':
        return 'bridge'
    # This is a bit of a last resort.  It'd be nice to always be able
    # to determine the correct type but unfortunately CL is not at all
    # consistent in this regard.
    if int_data['mode'] == 'NotConfigured':
        return None
    # We arrive here by process of elimination.  It's maybe a bit dodgy
    # but NETd will just reject whatever garbage we create, so it's
    # (mostly) safe.
    return 'vxlan'


def get_interface_master(summary: str) -> Optional[str]:
    """
    Parses the summary string from the interface to determine master
    device name.  If the string is parsed successfully the master
    device name is returned, otherwise None is returned.

    :param summary: Interface summary string.
    :return:
    """
    regex = r'^Master: (?P<master>[\w]*)\(.*\)$'
    if match := re.search(regex, summary):
        return match.group('master')
    else:
        return None


def get_base_command(int_name: str, int_type: str, action: str = 'add') -> str:
    """
    Generates the base command for interface configuration.

    :param int_name: The interface name.
    :param int_type: The interface type.
    :param action: The action to take, `add` or `del`.
    :return:
    """
    if action not in ['add', 'del']:
        raise Exception("`action` must be `add` or `del`.")
    if int_type == 'vlan':
        vlan_id = parse_svi_name(int_name)
        return f'{action} {int_type} {vlan_id}'
    else:
        return f'{action} {int_type} {int_name}'


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
    parent = None
    if int_data['iface_obj']['vlan_list']:
        mode = 'bridged'
        attributes = get_bridge_attributes(int_data)
    elif int_data['mode'] == 'BondMember':
        mode = 'aggregated'
        attributes = None
        parent = get_interface_master(int_data['summary'])
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
        parent=parent,
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
        int_type = get_interface_type(cur_int_name, int_data)
        if int_name and int_name != cur_int_name:
            continue
        if int_type in ['interface', 'bond']:
            interfaces.append(
                get_interface(cur_int_name, int_data, None, vrf_list))
        if int_type == 'vlan':
            subint_name = f"{int_name}-v0"
            if subint_name in show_int_data:
                subint_data = show_int_data[subint_name]
            else:
                subint_data = None
            interfaces.append(
                get_interface(cur_int_name, int_data, subint_data, vrf_list)
            )

    return interfaces


def generate_bridge_commands(attributes: an_if.InterfaceBridgeAttributes,
                             add_base: str, del_base: str) -> [str]:
    """
    Generate a list of commands to configure an interface for bridging.

    :param attributes: An :py:class:`InterfaceBridgeAttributes` object.
    :param add_base: The base command returned from
        :py:func:`get_base_command` for configuration adds.
    :param del_base: The base command returned from
        :py:func:`get_base_command` for configuration deletes.
    :return:
    """
    commands = []
    if attributes.dot1q_enabled:
        commands.append(f'{del_base} bridge access')
        if attributes.dot1q_pvid:
            commands.append(f'{add_base} bridge pvid {attributes.dot1q_pvid}')
        if attributes.dot1q_vids:
            vlan_glob = vlan_list_to_glob(attributes.dot1q_vids)
            commands.append(f'{add_base} bridge trunk vlans {vlan_glob}')
    else:
        commands.append(f'{del_base} bridge trunk')
        commands.append(f'{del_base} bridge pvid')
        commands.append(f'{add_base} bridge access {attributes.dot1q_pvid}')

    return commands


def generate_route_commands(attributes: an_if.InterfaceRouteAttributes,
                            add_base: str, del_base: str) -> [str]:
    """
    Generate a list of commands to configure an interface for routing.

    :param attributes: An :py:class:`InterfaceRouteAttributes` object.
    :param add_base: The base command returned from
        :py:func:`get_base_command` for configuration adds.
    :param del_base: The base command returned from
        :py:func:`get_base_command` for configuration deletes.
    :return:
    """
    commands = []
    if attributes.vrf:
        commands.append(f'{add_base} vrf {attributes.vrf}')
    for address in attributes.addresses:
        af = 'ip' if address.family == 'ipv4' else 'ipv6'
        if address.virtual and address.virtual_type == 'anycast':
            address_type = 'address-virtual'
            mac = f"{attributes.evpn_anycast_mac} ".lower().replace('-', ':')
        else:
            address_type = 'address'
            mac = ''
        commands.append(f'{add_base} {af} {address_type} {mac}{address.address}')
    return commands


def generate_basic_interface_commands(interface: an_if.Interface,
                                      add_base: str, del_base: str) -> [str]:
    """
    Generate a list of commands that will configure basic interface
    attributes such as MTU and description.

    :param interface:  An :py:class:`Interface` object.
    :param add_base: The base command returned from
        :py:func:`get_base_command` for configuration adds.
    :param del_base: The base command returned from
        :py:func:`get_base_command` for configuration deletes.
    :return:
    """
    commands = [add_base]
    if interface.admin_enabled is False:
        commands.append(f'{add_base} link down')
    if interface.admin_enabled is True:
        commands.append(f'{del_base} link down')
    if interface.mtu:
        commands.append(f'{add_base} mtu {interface.mtu}')
    if interface.description:
        commands.append(f'{add_base} alias "{interface.description}"')
    if 'interface' in add_base and interface.speed:
        commands.append(f'{add_base} link speed {interface.speed}')
    return commands


def generate_create_interface_commands(interface: an_if.Interface,
                                       int_type: str) -> [str]:
    """
    Generate a list of commands required to create an interface
    configuration from unconfigured state.

    :param interface: An :py:class:`Interface` object.
    :param int_type: An interface type returned from
        :py:func`get_interface_type`.
    :return:
    """
    add_base = get_base_command(interface.name, int_type, 'add')
    del_base = get_base_command(interface.name, int_type, 'del')

    commands = generate_basic_interface_commands(
        interface, add_base, del_base)
    if interface.mode == 'routed':
        # An SVI may have had IP forwarding disabled as part of a
        # VXLAN binding.  We turn it back on here.
        if int_type == 'vlan':
            commands.append(f'{del_base} ip forward off')
        commands += generate_route_commands(
            interface.attributes, add_base, del_base)
    if interface.mode == 'bridged':
        commands += generate_bridge_commands(
            interface.attributes, add_base, del_base)

    return commands


def generate_update_interface_commands(interface: an_if.Interface,
                                       int_type: str,
                                       update: bool = False) -> [str]:
    """
    Generate a list of commands required to update an interface.

    :param interface: An :py:class:`interface` object.
    :param int_type: An interface type returned from
        :py:func`get_interface_type`.
    :param update: Indicate that the interface is to be updated instead
        of overwritten.
    :return:
    """
    # If we are doing a replacement instead of an update, we just remove
    # the interface configuration and then replace it.
    del_base = get_base_command(interface.name, int_type, 'del')
    add_base = get_base_command(interface.name, int_type, 'add')
    if not update:
        # We made sure to omit default delete for bonds.
        del_commands = [del_base] if not int_type == 'bond' else []
        create_commands = generate_create_interface_commands(interface,
                                                             int_type)
        return del_commands + create_commands
    # Otherwise, we work through the interface object and generate a list of
    # commands to perform an update.
    else:
        commands = generate_basic_interface_commands(
            interface, add_base, del_base)

        if interface.mode == 'bridged' and interface.attributes:
            commands += generate_bridge_commands(
                interface.attributes, add_base, del_base)
        if interface.mode == 'routed' and interface.attributes:
            commands += generate_route_commands(
                interface.attributes, add_base, del_base)
        return commands


def generate_create_commands(interface: an_if.Interface,
                             int_type: str) -> [str]:
    """
    Generate a list of commands required to create an interface.

    :param interface: An :py:class:`Interface` object.
    :param int_type: The type of interface, vlan, bond, vrf, etc.
    :return:
    """
    # Currently, we only support creating SVIs.  We have this logic
    # fork here in anticipation of supporting other types later on.
    if int_type == 'vlan':
        return generate_create_interface_commands(interface, int_type)

    return []


def generate_update_commands(interface: an_if.Interface, int_type: str,
                             update: bool = False) -> [str]:
    """
    Generate a list of commands required to update an interface's
    configuration.

    :param interface: An :py:class:`Interface` object.
    :param int_type: The type of interface, vlan, bond, vrf, etc.
    :param update: When True, unset interface properties will be
        ignored instead of overwritten with default values.
    :return:
    """
    if int_type in ['vlan', 'interface', 'bond']:
        return generate_update_interface_commands(interface, int_type, update)
    else:
        return []


def generate_delete_commands(int_name: str, int_type: str) -> [str]:
    """
    Create a list of commands to destroy or reset and interface, as
    appropriate.

    :param int_name: The interface name.
    :param int_type: The interface type.
    :return:
    """
    return [get_base_command(int_name, int_type, 'del')]

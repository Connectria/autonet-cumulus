from autonet.core.objects import lag as an_lag
from autonet.util.evpn import parse_esi


def get_evpn_es_map(show_evpn_es_data: dict) -> dict:
    """
    Parses the output of the :code:`show evpn es` command into a
    mapping of interface to ES value so that it can be easily
    referenced.

    :param show_evpn_es_data: Output from the :code:`show evpn es`
        command.
    :return:
    """
    evpn_es_map = {}
    for evpn_es in show_evpn_es_data:
        if 'accessPort' in evpn_es:
            evpn_es_map[evpn_es['accessPort']] = evpn_es['esi']

    return evpn_es_map


def get_lags(show_bonds_data: dict, show_evpn_es_data: dict = None,
             bond_name: str = None) -> [an_lag.LAG]:
    """
    Returns a list of LAGs configured on the device.

    :param show_bonds_data: Output from the
        :code:`show interface bonds` command.
    :param show_evpn_es_data: Output from the :code:`show evpn es`
        command.
    :param bond_name: Filter results for the specified bond name.
    :return:
    """
    evpn_es_map = get_evpn_es_map(show_evpn_es_data)
    bonds = []
    for bond_data_name, bond_data in show_bonds_data.items():
        if bond_name and bond_name != bond_data_name:
            continue
        evpn_esi = None
        if bond_data_name in evpn_es_map:
            evpn_esi = evpn_es_map[bond_data_name]
        iface_obj = show_bonds_data[bond_data_name]['iface_obj']
        bonds.append(an_lag.LAG(
            name=bond_data_name,
            members=[x for x in iface_obj['members']],
            evpn_esi=evpn_esi
        ))
    return bonds


def generate_create_lag_commands(lag: an_lag.LAG) -> [str]:
    """
    Generate a list of commands needed to create a new
    LAG interface.

    :param lag: A :py:class:`LAG` object.
    :return:
    """
    commands = [f'add bond {lag.name} bond mode 802.3ad']
    commands += [f'del interface {member}' for member in lag.members]
    commands += [f'add interface {member}' for member in lag.members]
    commands += [f'add bond {lag.name} bond slaves {member}'
                 for member in lag.members]
    if lag.evpn_esi:
        parsed_esi = parse_esi(lag.evpn_esi)
        if parsed_esi['type'] != 3:
            raise Exception("Could not process ESI.")
        es_id = parsed_esi['local_discriminator']
        es_sys_mac = parsed_esi['system_mac']
        commands.append(f'add bond {lag.name} evpn mh es-id {es_id}')
        commands.append(f'add bond {lag.name} evpn mh es-sys-mac {es_sys_mac}')

    return commands


def generate_delete_lag_commands(lag_name: str) -> [str]:
    """
    Generate a list of commands needed to delete a bond
    interface.

    :param lag_name: The name of the bond interface.
    :return:
    """
    return [f'del bond {lag_name}']
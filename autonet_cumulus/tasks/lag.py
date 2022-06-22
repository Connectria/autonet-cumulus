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


def generate_lag_esi_commands(lag: an_lag.LAG) -> [str]:
    """
    Generate the commands required to set a Type 3 ESI.

    :param lag: A :py:class:`LAG` object.
    :return:
    """
    parsed_esi = parse_esi(lag.evpn_esi)
    if parsed_esi['type'] != 3:
        raise Exception("Could not process ESI.")
    es_id = parsed_esi['local_discriminator']
    es_sys_mac = parsed_esi['system_mac']
    return [f'add bond {lag.name} evpn mh es-id {es_id}',
            f'add bond {lag.name} evpn mh es-sys-mac {es_sys_mac}']


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
        commands += generate_lag_esi_commands(lag)

    return commands


def generate_update_lag_commands(lag: an_lag, original_lag: an_lag, update: bool) -> [str]:
    """
    Generate a list of commands to update or create a LAG, as
    appropriate.

    :param lag: A :py:class:`LAG` object representing the desired bond
        configuration.
    :param original_lag: A :py:class:`LAG` object representing the
        current bond configuration.
    :param update: When True no commands are generated for fields
        that are set to None.
    :return:
    """
    # If members is set, or we are doing a replacement operation.
    commands = [f'add bond {lag.name} bond mode 802.3ad']
    if lag.members or not update:
        # keep_members are members that will remain in the bond.
        keep_members = []
        if original_lag:
            keep_members = [member for member in lag.members
                            if member in original_lag.members]
        # If the member is new to the bond, we flush its configuration.
        commands += [f'del interface {member}' for member in lag.members
                     if member not in keep_members]
        # We explicitly add all new members, even if they already exist
        # because the operation is idempotent.
        commands += [f'add interface {member}' for member in lag.members]
        commands += [f'add bond {lag.name} bond slaves {member}'
                     for member in lag.members]
    # Find members to remove on a replace operation and there's an
    # existing lag.
    if lag.members and not update and original_lag:
        remove_members = [member for member in original_lag.members
                          if member not in lag.members]
        commands += [f'del bond {lag.name} bond slaves {member}'
                     for member in remove_members]
        commands += [f'del interface {member}' for member in remove_members]

    if lag.evpn_esi:
        commands += generate_lag_esi_commands(lag)
    # If it's a replace operation, we explicitly remove the configuration.
    elif not update:
        commands += [f'del bond {lag.name} evpn mh es-id',
                     f'del bond {lag.name} evpn mh es-sys-mac']

    return commands


def generate_delete_lag_commands(lag_name: str) -> [str]:
    """
    Generate a list of commands needed to delete a bond
    interface.

    :param lag_name: The name of the bond interface.
    :return:
    """
    return [f'del bond {lag_name}']

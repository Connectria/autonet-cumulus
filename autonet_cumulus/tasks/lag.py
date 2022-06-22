from autonet.core.objects import lag as an_lag


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

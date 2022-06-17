from autonet.core.objects import vlan as an_vlan
from typing import Union


def get_vlans(vlan_data: dict, bridge: str, dynamic_vlans: [int],
              vlan_id: Union[str, int] = None, show_dynamic: bool = False,
              ) -> [an_vlan.VLAN]:
    """
    Returns a list of :py:class:`VLAN` objects.  VLAN IDs
    that fall in the range of reserved VLANs will be omitted by
    default.

    :param vlan_data: Output from the :code:`show bridge vlan` command.
    :param bridge: The primary bridge name.
    :param dynamic_vlans: A list of VLAN IDs reserved for dynamic
        allocation.
    :param vlan_id: Filter results for the given VLAN ID.
    :param show_dynamic: Include dynamic VLANs in the response.
    :return:
    """
    vlan_id = int(vlan_id) if vlan_id else None
    vlans = []
    for vlan_obj in vlan_data[bridge]:
        start = vlan_obj['vlan']
        stop = int(vlan_obj.get('vlanEnd', start)) + 1
        for vid in range(start, stop):
            if vid in dynamic_vlans and not show_dynamic:
                continue
            if vlan_id and vid != vlan_id:
                continue
            vlans.append(an_vlan.VLAN(id=vid, admin_enabled=True))

    return vlans


def generate_create_vlan_commands(vlan: an_vlan.VLAN, bridge: str) -> [str]:
    """
    Generate a list of commands to create a vlan on the bridge.  If the
    VLAN exists in the defined dynamic range, nothing will be returned.

    :param vlan: A :py:class:`VLAN` object.
    :param bridge: The primary bridge name.
    :return:
    """
    return [f"add bridge {bridge} vids {vlan.id}"]


def generate_delete_vlan_commands(vlan_id: Union[str, int],
                                  bridge: str) -> [str]:
    """
    Generate a list of commands to delete a vlan from the bridge.  If
    the VLAN exists in the defined dynamic range, nothing will be
    returned.

    :param vlan_id: The VLAN ID to delete.
    :param bridge: The primary bridge name.
    :return:
    """
    return [f"del bridge {bridge} vids {vlan_id}"]
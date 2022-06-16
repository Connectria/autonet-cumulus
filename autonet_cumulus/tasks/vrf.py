import re

from autonet.core.objects import vrf as an_vrf


def get_vrfs(ip_vrf_data: str, vrf_name: str = None) -> [an_vrf.VRF]:
    """
    Get a list of :py:class:`VRF` objects.

    :param ip_vrf_data: The output of the
        :code:`ip -o link show type vrf` command.
    :param vrf_name: Filter for a particular VRF by name.
    :return:
    """
    vrfs = []
    regex = r'^(?P<ifidx>[\d]*): (?P<ifname>[\S]*):'
    for line in ip_vrf_data.split("\n"):
        if matches := re.search(regex, line):
            if_name = matches.group('ifname')
            if vrf_name and vrf_name != if_name:
                continue
            vrfs.append(an_vrf.VRF(name=if_name, ipv4=True, ipv6=True,
                                   export_targets=[], import_targets=[]))
    return vrfs


def generate_create_vrf_commands(vrf: an_vrf.VRF) -> [str]:
    """
    Generates the commands required to create a VRF.

    :param vrf: A :py:class`VRF` object.
    :return:
    """
    return [f'add vrf {vrf.name}']


def generate_delete_vrf_commands(vrf_name: str) -> [str]:
    """
    Generate a list of commands to delete a vrf.

    :param vrf_name: The name of the VRF to be removed.
    :return:
    """
    return [f'del vrf {vrf_name}']

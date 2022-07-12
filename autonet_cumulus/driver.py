import logging
import random
import re

from autonet.config import config
from autonet.core.device import AutonetDevice
from autonet.core import exceptions as exc
from autonet.core.objects import interfaces as an_if
from autonet.core.objects import lag as an_lag
from autonet.core.objects import vlan as an_vlan
from autonet.core.objects import vrf as an_vrf
from autonet.core.objects import vxlan as an_vxlan
from autonet.drivers.device.driver import DeviceDriver
from autonet.util.config_string import glob_to_vlan_list
from autonet.util.evpn import parse_esi
from conf_engine.options import StringOption
from json import loads as json_loads
from json.decoder import JSONDecodeError
from ipaddress import ip_interface
from pssh.clients import SSHClient
from typing import List, Optional, Tuple, Union

from autonet_cumulus.commands import CommandResult, CommandResultSet
from autonet_cumulus.tasks import interface as if_task
from autonet_cumulus.tasks import lag as lag_task
from autonet_cumulus.tasks import vlan as vlan_task
from autonet_cumulus.tasks import vrf as vrf_task
from autonet_cumulus.tasks import vxlan as vxlan_task

cl_opts = [
    StringOption('dynamic_vlans', default='4000-4094'),
    StringOption('bridge_name', default='')
]
config.register_options(cl_opts, 'cumulus_linux')


class CumulusDriver(DeviceDriver):
    def __init__(self, device: AutonetDevice):
        self._connection = SSHClient(
            str(device.address),
            user=device.credentials.username,
            password=device.credentials.password
        )
        self._result_cache = CommandResultSet()
        self._device = device
        self._version_data = None
        super().__init__(device)

    @property
    def dynamic_vlans(self) -> [int]:
        """
        A list of integers that represent VLAN IDs that have been
        reserved for dynamic allocation.

        :return:
        """
        vlan_glob = self.device.metadata.get(
            'dynamic_vlans', config.cumulus_linux.dynamic_vlans)
        return glob_to_vlan_list(vlan_glob)

    @property
    def bridge(self) -> str:
        """
        Return the name of the bridge device.  If the bridge name is
        explicitly configured, that will be used.  Otherwise, the
        bridge name will be inferred from the first bridge defined.

        :return:
        """
        # Try to get it from metadata, then default to config if it is
        # not there.
        if bridge := self.device.metadata.get(
                'bridge_name', config.cumulus_linux.bridge_name):
            return bridge
        # Otherwise, attempt to figure it out.
        stdout, _ = self._exec_raw_command('ip -o link show type bridge')
        regex = r'^(?P<ifidx>[\d]*): (?P<ifname>[\S]*):'
        matches = re.search(regex, stdout)
        return matches.group('ifname')

    @property
    def loopback_address(self):
        """
        Returns the first IPv4 /32 address attached to the loopback
        interface. An exception is raised if the loopback cannot
        be found.

        :return:
        """
        show_int_command = 'show interface lo'
        show_int_result = self._exec_net_commands([show_int_command])
        show_int_data = show_int_result.get(show_int_command).json
        for address in show_int_data['iface_obj']['ip_address']['allentries']:
            ip_int = ip_interface(address)
            if ip_int.version == 4 and not ip_int.is_loopback:
                return str(ip_int.ip)
        raise Exception("Could not find loopback address.")

    @property
    def version(self) -> str:
        """
        The OS version string.

        :return:
        """
        version_command = 'show version'
        version_result = self._exec_net_commands([version_command])
        return version_result.get(version_command).json['os']

    @property
    def major_version(self) -> int:
        """
        The OS major version number.
        :return:
        """
        return int(self.version.split('.')[0])

    @property
    def minor_version(self) -> int:
        """
        The OS Minor version number.
        :return:
        """

        return int(self.version.split('.')[1])

    @property
    def evpn_mh_supported(self) -> bool:
        """
        Indicate that the device has support for EVPN MH.

        :return:
        """
        supported_version = self.major_version >= 4 and self.minor_version >= 2
        show_system_commands = 'show system'
        show_system_result = self._exec_net_commands([show_system_commands])
        system_data = show_system_result.get(show_system_commands).json
        supported_platform = False
        if 'info' in system_data['platform']:
            soc_data = system_data['platform']['info']['soc']
            supported_platform = soc_data['vendor'] == "Mellanox"
        else:
            supported_platform = system_data['platform']['model'] == 'VX'

        return supported_platform and supported_version

    @staticmethod
    def _format_net_command(command: str, json: bool) -> str:
        """
        Properly formats a NETd command.

        :param command: The command to set to NETd.
        :param json: Indicate if JSON output is desired.
        :return:
        """
        # Ensure command starts with 'net '.
        if not command.startswith('net '):
            command = f"net {command}"
        # Ensure command requests json.
        if json and not command.endswith(' json'):
            command = f"{command} json"
        return command

    def _exec_raw_command(self, command: str) -> Tuple[str, str]:
        """
        Execute a raw command on the device and returns the raw output.
        Returns a tuple of stdout, and stderr strings.

        :param command: The command to execute.
        :return:
        """
        # return self._connection.run(command)
        result = self._connection.run_command(command, use_pty=True)
        return "\n".join(list(result.stdout)), "\n".join(list(result.stderr))

    def _exec_net_commands(self, commands: [str], json: bool = True,
                           cache: bool = True) -> CommandResultSet:
        """
        Executes a list of NETd commands on the device and returns a
        list of results.  Attempt will be made to send the command
        requesting output formatted as  JSON unless :py:attr:`json` is
        set to False.  JSON results will be returned already parsed by
        :py:meth:`json.loads()`.

        :param commands: A list of commands to be executed.
        :param json: Attempt to get the command's JSON output and parse
            it accordingly.
        :param cache: Search the command result cache for previously
            cached results for the same command.
        :return:
        """
        results = CommandResultSet()
        for command in commands:
            # If we already issued the command, then we'll look in our
            # cache for it unless dictated otherwise.
            if cache:
                if cached_result := self._result_cache.get(command):
                    results.append(cached_result)
                    continue
            # Otherwise, try and fetch the result ourselves.
            original_command = command
            command = self._format_net_command(command, json)

            # Prep result class
            result = CommandResult(command, original_command)
            stdout, stderr = self._exec_raw_command(result.command)
            result.stdout = stdout
            result.stderr = stderr
            if json:
                try:
                    result.json = json_loads(stdout)
                except JSONDecodeError:
                    pass
            # Append the result to our return value, as well as to
            # our cache.
            results.append(result)
            self._result_cache.append(result)

        return results

    def _exec_config_abort(self) -> CommandResultSet:
        """
        Executes the `net abort` command and returns the
        result set.

        :return:
        """
        return self._exec_net_commands(['abort'], False, False)

    def _exec_config_commands(self, commands: [str]) -> CommandResultSet:
        """
        Executes a list of configuration commands.  Once the commands
        are applied an attempt to execute a commit will be performed.
        If the commit fails an attempt to execute a config abort will
        be made and an exception will be raised.

        :param commands:
        :return:
        """
        config_results = self._exec_net_commands(commands, False, False)
        commit_results = self._exec_net_commands(['commit'], False, False)
        commit_result = commit_results.get('commit')
        if commit_result.stderr or commit_result.stdout.startswith('ERROR:'):
            self._exec_config_abort()
            logging.error("An error was encountered with the following "
                          f"config set: {commands}"
                          f"STDOUT: \n{commit_result.stdout}"
                          f"STDERR: \n{commit_result.stderr}")
            raise exc.AutonetException(f"Driver {self} encountered an error "
                                       "attempting to apply the requested"
                                       "configuration.  Pending configuration"
                                       "rollback has been performed.")
        config_results.append(commit_results.get('commit'))

        return config_results

    def _get_interface_type(self, int_name) -> str:
        """
        Gets the type of interface, vlan, bond, vrf, etc.

        :param int_name: The name of the interface
        :return:
        """
        show_int_command = f'show interface {int_name}'
        results = self._exec_net_commands([show_int_command])
        int_data = results.get(show_int_command)
        return if_task.get_interface_type(int_name, int_data.json)

    def _get_vxlan_data(self) -> dict:
        """
        Collect data about VXLAN configuration from several commands
        and return a parsed object containing information that can be
        used by various other methods.

        :return:
        """
        evpn_vni_command = 'show evpn vni'
        bgp_evpn_command = 'show bgp evpn vni'
        vlan_data_command = 'show bridge vlan'
        commands = [evpn_vni_command, bgp_evpn_command, vlan_data_command]
        results = self._exec_net_commands(commands)
        return vxlan_task.parse_vxlan_data(
            results.get(evpn_vni_command).json,
            results.get(bgp_evpn_command).json,
            results.get(vlan_data_command).json
        )

    def _get_dynamic_vlan(self) -> int:
        """
        Get a vlan from the configured dynamic vlan pool.

        :return:
        """
        vlan_objects = self._bridge_vlan_read(show_dynamic=True)
        used_vlans = [vlan.id for vlan in vlan_objects]
        unused_dynamic_vlans = [vlan for vlan in self.dynamic_vlans
                                if vlan not in used_vlans]
        return random.choice(unused_dynamic_vlans)

    def _get_bgp_evpn_data(self) -> dict:
        """
        Collects the BGP ASN and router ID for the EVPN address family
        and returns them in a dictionary.

        :return:
        """
        show_bgp_command = 'show bgp evpn summary'
        show_bgp_result = self._exec_net_commands([show_bgp_command])
        evpn_data = show_bgp_result.get(show_bgp_command).json
        return {
            'asn': evpn_data['as'],
            'rid': evpn_data['routerId']
        }

    def _interface_read(self, request_data: str = None, cache=True) -> [an_if.Interface]:
        show_int_command = 'show interface'
        results = self._exec_net_commands([show_int_command], cache=cache)
        interfaces = if_task.get_interfaces(
            results.get(show_int_command).json,
            int_name=request_data)
        if len(interfaces) == 1 and request_data:
            return interfaces[0]
        else:
            return interfaces

    def _interface_create(self, request_data: an_if.Interface) -> an_if.Interface:
        # CL doesn't allow creation of loopbacks, and we're not going to support
        # sub interfaces at the moment, so here we are with VLANs or bust.
        int_type = self._get_interface_type(request_data.name)
        if not int_type == 'vlan':
            raise exc.DriverRequestError()
        elif request_data.mode == 'bridged':
            raise exc.DeviceOperationUnsupported(
                driver=self, device_id=self.device.device_id, operation="Bridge mode SVIs")

        commands = if_task.generate_create_commands(request_data, int_type)
        self._exec_config_commands(commands)
        return self._interface_read(request_data.name, cache=False)

    def _interface_update(self, request_data: an_if.Interface,
                          update) -> an_if.Interface:
        int_type = self._get_interface_type(request_data.name)
        # Cumulus has a hard time switching interface modes. To
        # work around this, the interface is deleted and recreated
        # using a merge of the existing configuration and the
        # configuration provided.  If the mode isn't changed then
        # those steps are skipped.
        current_config = self._interface_read(request_data.name)
        if update and request_data.mode and request_data.mode != current_config.mode:
            request_data = current_config.merge(request_data)
            self._interface_delete(request_data.name)
        # Pass to the command generator, and exec config.
        commands = if_task.generate_update_commands(request_data, int_type, update)
        self._exec_config_commands(commands)
        return self._interface_read(request_data.name, cache=False)

    def _interface_delete(self, request_data: str):
        int_type = self._get_interface_type(request_data)
        commands = if_task.generate_delete_commands(request_data, int_type)
        self._exec_config_commands(commands)

    def _bridge_vlan_read(self, request_data: Optional[Union[str, int]] = None,
                          show_dynamic: bool = False) -> Union[List[an_vlan.VLAN], an_vlan.VLAN]:
        vlan_data_command = 'show bridge vlan'
        vlan_data_results = self._exec_net_commands([vlan_data_command])
        vlan_data = vlan_data_results.get(vlan_data_command).json
        vlans = vlan_task.get_vlans(vlan_data, self.bridge, self.dynamic_vlans,
                                    request_data, show_dynamic)
        if request_data and len(vlans) == 1:
            return vlans[0]
        else:
            return vlans

    def _bridge_vlan_create(self, request_data: an_vlan.VLAN) -> an_vlan.VLAN:
        if request_data.id in self.dynamic_vlans:
            raise exc.DriverOperationUnsupported(
                self, "Requested VLAN ID is reserved.")
        commands = vlan_task.generate_create_vlan_commands(
            request_data, self.bridge)
        self._exec_config_commands(commands)
        return an_vlan.VLAN(id=request_data.id, admin_enabled=True)

    def _bridge_vlan_delete(self, request_data: str) -> None:
        if int(request_data) in self.dynamic_vlans:
            raise exc.DriverOperationUnsupported(
                self, "Requested VLAN ID is reserved.")
        commands = vlan_task.generate_delete_vlan_commands(
            request_data, self.bridge)

        self._exec_config_commands(commands)

    def _vrf_read(self, request_data: str = None) -> Union[List[an_vrf.VRF], an_vrf.VRF]:
        ip_vrf_data, _ = self._exec_raw_command('ip -o link show type vrf')
        vrfs = vrf_task.get_vrfs(ip_vrf_data, request_data)
        if request_data and len(vrfs) == 1:
            return vrfs[0]
        return vrfs

    def _vrf_create(self, request_data: an_vrf.VRF) -> an_vrf.VRF:
        commands = vrf_task.generate_create_vrf_commands(request_data)
        self._exec_config_commands(commands)
        return self._vrf_read(request_data.name)

    def _vrf_delete(self, request_data: str) -> None:
        commands = vrf_task.generate_delete_vrf_commands(request_data)
        self._exec_config_commands(commands)

    def _tunnels_vxlan_read(self, request_data: str = None) -> Union[List[an_vxlan.VXLAN], an_vxlan.VXLAN]:
        vxlan_data = self._get_vxlan_data()
        vxlans = vxlan_task.get_vxlans(vxlan_data, request_data)
        if request_data and len(vxlans) == 1:
            return vxlans[0]
        return vxlans

    def _tunnels_vxlan_create(self, request_data: an_vxlan.VXLAN) -> an_vxlan.VXLAN:
        dynamic_vlan = self._get_dynamic_vlan() if request_data.layer == 3 else None
        bgp_data = self._get_bgp_evpn_data()

        # We default to no ip forwarding and enable it only if the VLAN exists.
        ip_forward = False
        if request_data.layer == 2 and self._bridge_vlan_read(request_data.bound_object_id):
            ip_forward = True

        commands = vxlan_task.generate_create_vxlan_commands(
            request_data, self.loopback_address, bgp_data, dynamic_vlan, ip_forward)
        self._exec_config_commands(commands)
        return self._tunnels_vxlan_read(str(request_data.id))

    def _tunnels_vxlan_delete(self, request_data: str) -> None:
        vxlan_data = self._get_vxlan_data()
        commands = vxlan_task.generate_delete_vxlan_commands(request_data, vxlan_data)
        self._exec_config_commands(commands)

    def _interface_lag_read(self, request_data: str, cache=True) -> Union[List[an_lag.LAG], an_lag.LAG]:
        show_bonds_command = 'show interface bonds'
        show_evpn_es_command = 'show evpn es'
        command_results = self._exec_net_commands([show_bonds_command,
                                                   show_evpn_es_command], cache=cache)
        show_bonds_data = command_results.get(show_bonds_command).json
        show_evpn_es_data = command_results.get(show_evpn_es_command).json
        bonds = lag_task.get_lags(show_bonds_data, show_evpn_es_data, request_data)
        if request_data and len(bonds) == 1:
            return bonds[0]
        return bonds

    def _interface_lag_create(self, request_data: an_lag.LAG) -> an_lag.LAG:
        if request_data.evpn_esi:
            if not self.evpn_mh_supported:
                raise exc.DeviceOperationUnsupported(self, 'evpn_esi',
                                                     self.device.device_id)
            if parse_esi(request_data.evpn_esi)['type'] != 3:
                raise exc.DriverOperationUnsupported(
                    self, 'EVPN ESI must be Type 3.')
        commands = lag_task.generate_create_lag_commands(request_data)
        self._exec_config_commands(commands)
        return self._interface_lag_read(request_data.name, cache=False)

    def _interface_lag_update(self, request_data: an_lag.LAG, update: bool) -> an_lag.LAG:
        original_lag = self._interface_lag_read(request_data.name)
        commands = lag_task.generate_update_lag_commands(
            request_data, original_lag, update)
        self._exec_config_commands(commands)
        return self._interface_lag_read(request_data.name, cache=False)

    def _interface_lag_delete(self, request_data: str) -> None:
        commands = lag_task.generate_delete_lag_commands(request_data)
        self._exec_config_commands(commands)

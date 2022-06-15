import logging

from autonet.core.device import AutonetDevice
from autonet.core import exceptions as exc
from autonet.core.objects import interfaces as an_if
from autonet.core.objects import lag as an_lag
from autonet.core.objects import vlan as an_vlan
from autonet.core.objects import vrf as an_vrf
from autonet.core.objects import vxlan as an_vxlan
from autonet.drivers.device.driver import DeviceDriver
from json import loads as json_loads
from json.decoder import JSONDecodeError
from pssh.clients import SSHClient
from typing import Tuple

from autonet_cumulus.commands import CommandResult, CommandResultSet
from autonet_cumulus.tasks import interface as if_task


class CumulusDriver(DeviceDriver):
    def __init__(self, device: AutonetDevice):
        self._connection = SSHClient(
            str(device.address),
            user=device.credentials.username,
            password=device.credentials.password
        )
        self._result_cache = CommandResultSet()
        super().__init__(device)

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

    def _get_interface_type(self, int_name):
        """
        Gets the type of interface, vlan, bond, vrf, etc.

        :param int_name: The name of the interface
        :return:
        """
        show_int_command = f'show interface {int_name}'
        results = self._exec_net_commands([show_int_command])
        int_data = results.get(show_int_command)
        return if_task.get_interface_type(int_name, int_data)

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

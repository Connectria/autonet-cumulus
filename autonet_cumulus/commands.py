from dataclasses import dataclass, field
from typing import Optional, Union

class Commands:
    show_int = 'show interface'
    show_vrf_vni = 'show vrf vni'


@dataclass
class CommandResult(object):
    command: str
    original_command: str
    stdout: str = field(default="")
    stderr: str = field(default="")
    json: Optional[Union[dict, list]] = field(default=None)
    return_code: int = field(default=0)
    failed: bool = field(default=True)


class CommandResultSet(list):
    """
    Represents a set of results.  Provides a way to query for the
    results of a given command by passing the command index, or the
    command itself, to :py:meth:`get()`.
    """

    def get(self, command: str) -> Optional[CommandResult]:
        """
        Searches the result set for a given :py:class:`CommandResult` based
        on the command issued.

        :param command: The command to search for.
        :return:
        """
        for result in self:
            if result.command == command or result.original_command == command:
                return result
        return None


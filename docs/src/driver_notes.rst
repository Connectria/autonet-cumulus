Driver Behavior Notes
=====================

  * When performing updates to existing interface where the interface
    mode changes the driver will perform a full wipe and commit of the
    interface configuration.  This may cause the operation to take
    additional time depending on the size of the switch configuration.

  * EVPN Anycast GW support is present and requires that the anycast
    gateway MAC address be sent as part of the
    :py:class:`InterfaceRouteAttributes` when making interface requests
    to configure an anycast address.
Driver Behavior Notes
=====================

Interfaces
----------

  * When performing updates to existing interface where the interface
    mode changes the driver will perform a full wipe and commit of the
    interface configuration.  This may cause the operation to take
    additional time depending on the size of the switch configuration.

  * EVPN Anycast GW support is present and requires that the anycast
    gateway MAC address be sent as part of the
    :py:class:`InterfaceRouteAttributes` when making interface requests
    to configure an anycast address.

VLANs
-----

  * Creating a VLAN will return a valid response and apply the VLAN ID
    to the bridge device, but will have no real effect.  Subsequent
    calls to read the VLAN will not show it present, nor will continued
    create requests fail with an :py:exc:`ObjectExists` error.  This is
    because Cumulus (and Linux) doesn't indicate the VLAN exists on a
    bridge device until there is an interface participating in that
    VLAN.

  * VLAN modification operations are unsupported.  Cumulus does not
    provided ability to name VLANs, nor set their operational state.

  * The Cumulus Linux driver has a configurable set of VLANs that are
    used for binding to EVPN L3VNIs.  VLAN operations that attempt to
    create or delete these VLANs will raise an exception.  See
    :doc:`configuration` for more information.
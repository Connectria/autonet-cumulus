Driver Configuration
====================

The Cumulus Linux driver registers its configuration options under the
`cumulus_linux` configuration group.  Options can be placed in the
group in any autonet `ini` style config file or may be set via
environment variables by prepending :code:`CUMULUS_LINUX_` to the
capitalized option name.

============= ========= ===============================================
Option        Default   Description
============= ========= ===============================================
dynamic_vlans 4000-4096 The `dynamic_vlans` option marks all VLANs
                        identified by a glob pattern as reserved for
                        dynamic allocation to L3VNI binding in EVPN
                        Symmetric raise an exception.
bridge_name             The bridge name to be used for VLAN operations.
                        If no name is supplied then the first bridge
                        returned by the device will be used.
============= ========= ===============================================


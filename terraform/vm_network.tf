resource "opennebula_virtual_network" "vm_network" {
  name            = "vnet"
  physical_device = "eth1"
  type            = "bridge"
  mtu             = 1500
  dns             = "77.88.8.8"
  gateway         = "10.13.180.10"
  network_address = "10.13.0.0"
  network_mask    = "255.255.0.0"
  security_groups = [0]
}

resource "opennebula_virtual_network_address_range" "vm_address_range" {
  virtual_network_id = opennebula_virtual_network.vm_network.id
  ar_type            = "IPV4"
  size               = 252
  ip4                = "10.13.80.1"
}

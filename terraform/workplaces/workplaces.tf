resource "opennebula_virtual_machine" "node-1" {
  for_each = local.addresses
  template_id = opennebula_template.node-1.id
  name     = "${each.key}"

  nic {
    network_id      = var.vm_nic_network_id
    security_groups = local.vm_nic_security_groups
    ip              = each.value
  }

  lifecycle {
    ignore_changes = [
      nic
    ]
  }
}

resource "opennebula_template" "node-1" {
  name = "node-1"
    cpu      = local.vm_cpu
    vcpu     = local.vm_vcpu
    memory   = local.vm_memory

  context = {
    NETWORK      = "YES"
  }

  graphics {
    type   = local.vm_graph_type
    listen = local.vm_graph_listen
  }

  os {
    arch = local.vm_os_arch
    boot = local.vm_os_boot
  }


  disk {
    image_id = data.opennebula_image.astra.id
    target = local.vm_disk_target
    driver = local.vm_disk_driver
    size = local.vm_disk_size
  }

  sched_requirements = "ID=\"${var.node_1}\""
}
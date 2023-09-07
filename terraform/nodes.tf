resource "opennebula_host" "node-1" {
  name = "10.13.180.10"
  type = "kvm"

  overcommit {
    cpu    = 4000
    memory = 67108864
  }
}

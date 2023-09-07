import mysql.connector
import xmlrpc.client
from xml.etree import ElementTree as ET
import string
import random
import subprocess
import os

server_url = "http://10.13.180.10:2633/RPC2"
login = "oneadmin"
password = "Toor301!"

mysql_host = "10.13.180.100"
mysql_user = "guacamole_user"
mysql_password = "guacamole_password"
mysql_database = "guacamole_db"

IP_FILE = '/root/used_ips.txt'

def generate_password(length):
    symbols = string.ascii_lowercase + string.digits
    return ''.join(random.choice(symbols) for _ in range(length))

def get_data():
    def extract_vm_data(xml_data):
        root = ET.fromstring(xml_data)
        vms = []
        for vm in root.findall('VM'):
            name = vm.find('NAME').text
            ip = vm.find('TEMPLATE/NIC/IP').text
            vms.append((name, ip))
        return vms

    with xmlrpc.client.ServerProxy(server_url) as server:
        response = server.one.vmpool.info(f"{login}:{password}", -2, -1, -1, -1)
        if len(response) == 1:
            print("Ошибка при получении списка виртуальных машин: ", response[0])
        else:
            vms = extract_vm_data(response[1])
    return vms

def update_database(vm_name, ip_address, password):
    mydb = mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database
    )

    cursor = mydb.cursor()

    cursor.execute(f"SELECT * FROM guacamole_entity WHERE name = '{vm_name}';")
    if cursor.fetchone() is not None:
        return
    
    cursor.execute("SELECT UNHEX(SHA2(UUID(), 256));")
    salt = cursor.fetchone()[0]
    cursor.execute("INSERT INTO guacamole_entity (name, type) VALUES (%s, 'USER');", (vm_name,))
    cursor.execute("INSERT INTO guacamole_user (entity_id, password_salt, password_hash, password_date) SELECT entity_id, %s, UNHEX(SHA2(CONCAT(%s, HEX(%s)), 256)), CURRENT_TIMESTAMP FROM guacamole_entity WHERE name = %s AND type = 'USER';", (salt, password, salt, vm_name))
    cursor.execute("INSERT INTO guacamole_connection (connection_name, protocol) VALUES (%s, 'rdp');", (vm_name,))
    cursor.execute("SET @connid = (SELECT connection_id FROM guacamole_connection WHERE connection_name = %s);", (vm_name,))
    cursor.execute("SET @uid = (SELECT entity_id FROM guacamole_entity WHERE name = %s);", (vm_name,))
    cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'hostname', %s);", (ip_address,))
    cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'port', '3389');")
    cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'username', 'astra');")
    cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'password', 'toor');")
    cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'height', '1080');")
    cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'width', '1920');")
    cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'ignore-cert', 'true');")
    cursor.execute("INSERT INTO guacamole_connection_permission VALUES (@uid, @connid, 'READ');")

    mydb.commit()
    cursor.close()
    mydb.close()

def generate_keys():
    private_key = subprocess.getoutput('wg genkey')
    public_key = subprocess.getoutput(f'echo "{private_key}" | wg pubkey')
    return private_key, public_key

def get_available_ip():
    used_ips = set()

    if os.path.exists(IP_FILE):
        with open(IP_FILE, 'r') as f:
            used_ips = set(f.read().splitlines())

    for i in range(2, 251):
        ip = f'10.8.0.{i}'
        if ip not in used_ips and not ip_address_exists(ip):
            return ip

    return None

def ip_address_exists(ip):
    config_files = os.listdir('/etc/wireguard/')
    for file_name in config_files:
        if file_name.endswith('.conf'):
            with open(f'/etc/wireguard/{file_name}') as f:
                lines = f.readlines()
                for line in lines:
                    if f'AllowedIPs = {ip}/32' in line:
                        return True
    return False

def create_config_file(client_name, private_key, public_key, server_public_key, server_ip, server_port):
    client_ip = get_available_ip()
    if client_ip is None:
        print('No available IP address.')
        return

    config = f"""
    [Interface]
    MTU = 1420
    PrivateKey = {private_key}
    Address = {client_ip}/32
    DNS = 8.8.8.8

    [Peer]
    PublicKey = {server_public_key}
    AllowedIPs = 0.0.0.0/0
    Endpoint = {server_ip}:{server_port}
    """

    with open(f'{client_name}.conf', 'w') as f:
        f.write(config.strip())

    with open('/etc/wireguard/wg-amsterdam.conf', 'a') as f:
        f.write(f'\n#{client_name}\n[Peer]\nPublicKey = {public_key}\nAllowedIPs = {client_ip}/32\n')

def main():
    vm_data = get_data()
    for vm in vm_data:
        name, ip = vm
        password = generate_password(8)
        print(f'Generated password for user {name}: {password}')
        update_database(name, ip, password)

        private_key, public_key = generate_keys()
        server_public_key = "{{ wireguard_clients_public_key }}"
        server_ip = "62.109.2.23"
        server_port = "51840"
        create_config_file(name, private_key, public_key, server_public_key, server_ip, server_port)

if __name__ == "__main__":
    main()

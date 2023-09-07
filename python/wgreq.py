import mysql.connector
import xmlrpc.client
from xml.etree import ElementTree as ET
import string
import random
import subprocess
import os

mysql_host = "10.13.180.100"
mysql_user = "guacamole_user"
mysql_password = "guacamole_password"
mysql_database = "guacamole_db"

IP_FILE = '/root/used_ips.txt'

def generate_password(length):
    symbols = string.ascii_lowercase + string.digits
    return ''.join(random.choice(symbols) for _ in range(length))

def get_data():
    conn = xmlrpc.client.ServerProxy("http://oneadmin:oneadmin@10.13.180.10:2633/RPC2")
    result = conn.one.vmpool.info(f"oneadmin:Toor301!", -2, -1, -1, -1)
    print(result)
    vm_data = xmlrpc.client.loads(result[1])
    return [(vm['ID'], vm['NAME'], vm['TEMPLATE']['NIC']['IP']) for vm in vm_data[0]]

def update_database(vm_id, vm_name, ip_address, password):
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
    cursor.execute(f"INSERT INTO guacamole_entity (name, type) VALUES ('{vm_name}', 'USER');")
    cursor.execute(f"INSERT INTO guacamole_user (entity_id, password_salt, password_hash, password_date) SELECT entity_id, {salt}, UNHEX(SHA2(CONCAT('{password}', HEX({salt})), 256)), CURRENT_TIMESTAMP FROM guacamole_entity WHERE name = '{vm_name}' AND type = 'USER';")
    cursor.execute(f"INSERT INTO guacamole_connection (connection_name, protocol) VALUES ('{vm_name}', 'rdp');")
    cursor.execute("SELECT connection_id FROM guacamole_connection WHERE connection_name = '{vm_name}';")
    connid = cursor.fetchone()[0]
    cursor.execute("SELECT entity_id FROM guacamole_entity WHERE name = '{vm_name}';")
    uid = cursor.fetchone()[0]
    cursor.execute(f"INSERT INTO guacamole_connection_parameter VALUES ({connid}, 'hostname', '{ip_address}');")
    cursor.execute(f"INSERT INTO guacamole_connection_parameter VALUES ({connid}, 'port', '3389');")
    cursor.execute(f"INSERT INTO guacamole_connection_parameter VALUES ({connid}, 'username', '{vm_name}');")
    cursor.execute(f"INSERT INTO guacamole_connection_parameter VALUES ({connid}, 'password', 'toor');")
    cursor.execute(f"INSERT INTO guacamole_connection_parameter VALUES ({connid}, 'height', '1080');")
    cursor.execute(f"INSERT INTO guacamole_connection_parameter VALUES ({connid}, 'width', '1920');")
    cursor.execute(f"INSERT INTO guacamole_connection_parameter VALUES ({connid}, 'ignore-cert', 'true');")
    cursor.execute(f"INSERT INTO guacamole_connection_permission VALUES ({uid}, {connid}, 'READ');")
    
    mydb.commit()

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
    data = get_data()
    for vm_id, vm_name, ip_address in data:
        password = generate_password(8)
        update_database(vm_id, vm_name, ip_address, password)

        private_key, public_key = generate_keys()
        server_public_key = "RRImilZD4HlwLBfKA4ZKNToXmWAuvyrwmbm3rGO1BgA="
        server_ip = "94.142.136.112"
        server_port = "51820"
        create_config_file(vm_name, private_key, public_key, server_public_key, server_ip, server_port)

if __name__ == "__main__":
    main()

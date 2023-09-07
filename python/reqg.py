import xmlrpc.client
from xml.etree import ElementTree as ET
import secrets
import string
import mysql.connector

server_url = "http://10.13.180.10:2633/RPC2"
login = "oneadmin"
password = "Toor301!"

db_host = "10.13.180.100"  # обновите с вашими данными
db_user = "guacamole_user"   # обновите с вашими данными
db_password = "guacamole_password" # обновите с вашими данными
db_name = "guacamole_db" # обновите с вашими данными

def generate_password(length):
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

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
        db_conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = db_conn.cursor()
        for vm in vms:
            password = generate_password(8)
            print(f'Generated password for user {vm[0]}: {password}')
            cursor.execute("SELECT UNHEX(SHA2(UUID(), 256));")
            salt = cursor.fetchone()[0]
            cursor.execute("INSERT INTO guacamole_entity (name, type) VALUES (%s, 'USER');", (vm[0],))
            cursor.execute("INSERT INTO guacamole_user (entity_id, password_salt, password_hash, password_date) SELECT entity_id, %s, UNHEX(SHA2(CONCAT(%s, HEX(%s)), 256)), CURRENT_TIMESTAMP FROM guacamole_entity WHERE name = %s AND type = 'USER';", (salt, password, salt, vm[0]))
            cursor.execute("INSERT INTO guacamole_connection (connection_name, protocol) VALUES (%s, 'rdp');", (vm[0],))
            cursor.execute("SET @connid = (SELECT connection_id FROM guacamole_connection WHERE connection_name = %s);", (vm[0],))
            cursor.execute("SET @uid = (SELECT entity_id FROM guacamole_entity WHERE name = %s);", (vm[0],))
            cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'hostname', %s);", (vm[1],))
            cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'port', '3389');")
            cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'username', 'astra');")
            cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'password', 'toor');")
            cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'height', '1080');")
            cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'width', '1920');")
            cursor.execute("INSERT INTO guacamole_connection_parameter VALUES (@connid, 'ignore-cert', 'true');")
            cursor.execute("INSERT INTO guacamole_connection_permission VALUES (@uid, @connid, 'READ');")
        db_conn.commit()
        cursor.close()
        db_conn.close()

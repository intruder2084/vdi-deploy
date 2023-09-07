SET @salt = UNHEX(SHA2(UUID(), 256));

INSERT INTO guacamole_entity (name, type) VALUES ('<user>', 'USER');

INSERT INTO guacamole_user (entity_id, password_salt, password_hash, password_date) SELECT entity_id, @salt, UNHEX(SHA2(CONCAT('<password>', HEX(@salt)), 256)), CURRENT_TIMESTAMP FROM guacamole_entity WHERE name = '9ks11-19-22' AND type = 'USER';

INSERT INTO guacamole_connection (connection_name, protocol) VALUES ('<connection_name>', 'rdp');

SET @connid = (SELECT connection_id FROM guacamole_connection WHERE connection_name = '<connection_name>');
SET @uid = (SELECT entity_id FROM guacamole_entity WHERE name = '<user>');

INSERT INTO guacamole_connection_parameter VALUES (@connid, 'hostname', '<address>');
INSERT INTO guacamole_connection_parameter VALUES (@connid, 'port', '3389');
INSERT INTO guacamole_connection_parameter VALUES (@connid, 'username', 'astra');
INSERT INTO guacamole_connection_parameter VALUES (@connid, 'password', 'toor');
INSERT INTO guacamole_connection_parameter VALUES (@connid, 'height', '1080');
INSERT INTO guacamole_connection_parameter VALUES (@connid, 'width', '1920');
INSERT INTO guacamole_connection_parameter VALUES (@connid, 'ignore-cert', 'true');

insert into guacamole_connection_permission values (@uid, @connid, 'READ');

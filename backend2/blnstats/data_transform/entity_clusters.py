import logging
import time
from datetime import datetime
from ..database.utils import get_db_connection
from ..database.raw_data_selector import RawDataSelector



# Configure logging
logger = logging.getLogger(__name__)



class EntityClusters:
    '''
    This class contains functions for creating and managing entity clusters in the Lightning_Entities table.
    '''


    def __init__(self):
        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:

                db_cursor.execute('''
                    CREATE TABLE IF NOT EXISTS `Lightning_Entities` (
                        `NodeID` CHAR(66) NOT NULL,
                        `EntityName` VARCHAR(255) NOT NULL,
                        CONSTRAINT `PRIMARY` PRIMARY KEY (`NodeID`)
                    );
                ''')

                db_cursor.execute('''
                    CREATE TABLE IF NOT EXISTS `Lightning_NodeAliases` (
                        `ID` INT AUTO_INCREMENT PRIMARY KEY,
                        `NodeID` CHAR(66) NOT NULL,
                        `Alias` VARCHAR(32) NOT NULL,
                        `firstSeen` TIMESTAMP NULL,
                        `lastSeen` TIMESTAMP NULL,
                        
                        UNIQUE KEY `unique_nodeid_alias` (`NodeID`, `Alias`),
                        INDEX `idx_nodeid` (`NodeID`),
                        INDEX `idx_alias` (`Alias`)
                    );
                ''')





    def import_node_aliases_to_main_table(self, from_table_name, from_alias_column, from_node_id_column, from_timestamp_column):
        '''
        This function imports node aliases into the Lightning_NodeAliases table from a source table.

        :param from_table_name: The name of the source table
        :param from_alias_column: The name of the alias column in the source table
        :param from_node_id_column: The name of the node ID column in the source table
        :param from_timestamp_column: The name of the timestamp column in the source table
        '''
        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:

                ##### Fetch all data from the source table
                logger.info(f'Fetching data from {from_table_name}')
                fetch_query = f'''
                    SELECT {from_node_id_column}, {from_alias_column}, {from_timestamp_column} FROM {from_table_name}
                '''
                db_cursor.execute(fetch_query)
                rows = db_cursor.fetchall()


                ##### Preprocess the data
                logger.info(f'Preprocessing data')
                processed_data = {}
                for row in rows:
                    node_id, alias, timestamp = row

                    # If the alias is empty, use the first 20 characters of the node_id
                    if(alias == ""):
                        alias = node_id[0:20]
                    

                    # If the timestamp is before the Lightning Network started, skip it
                    if(timestamp < datetime.fromisoformat('2017-12-01').timestamp()):
                        continue
                    # If the timestamp is in the future, skip it
                    elif(timestamp > time.time()):
                        continue
                    

                    timestamp_dt = datetime.fromtimestamp(timestamp)
                    
                    # Use a tuple of (node_id, alias) as the key
                    key = (node_id, alias)
                    
                    if key in processed_data:
                        # Update the first and last seen timestamps
                        first_seen, last_seen = processed_data[key]
                        processed_data[key] = (
                            min(first_seen, timestamp_dt),
                            max(last_seen, timestamp_dt)
                        )
                    else:
                        # Initialize the first and last seen timestamps
                        processed_data[key] = (timestamp_dt, timestamp_dt)

                # Convert the dictionary to a list of tuples for insertion
                processed_data_list = [
                    (node_id, alias, first_seen, last_seen)
                    for (node_id, alias), (first_seen, last_seen) in processed_data.items()
                ]


                ##### Insert processed data into the main table
                logger.info(f'Inserting processed data into the main table')
                insert_query = '''
                    INSERT INTO Lightning_NodeAliases (NodeID, Alias, firstSeen, lastSeen)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        firstSeen = LEAST(firstSeen, VALUES(firstSeen)),
                        lastSeen = GREATEST(lastSeen, VALUES(lastSeen))
                '''
                db_cursor.executemany(insert_query, processed_data_list)
                db_conn.commit()




    def import_new_entities_to_main_table(self):
        '''
        This function imports new entities into the Lightning_Entities table by selecting the latest alias for each NodeID from the Lightning_NodeAliases table.
        '''
        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:
                
                # Insert the latest alias for each NodeID into Lightning_Entities if it doesn't exist
                logger.info('Inserting new entities into Lightning_Entities')
                insert_query = '''
                    INSERT IGNORE INTO Lightning_Entities (NodeID, EntityName)
                    SELECT NodeID, Alias
                    FROM Lightning_NodeAliases
                    WHERE (NodeID, lastSeen) IN (
                        SELECT NodeID, MAX(lastSeen)
                        FROM Lightning_NodeAliases
                        GROUP BY NodeID
                    )
                '''
                db_cursor.execute(insert_query)
                db_conn.commit()
    




    def fix_entity_hex_names_if_possible(self):
        '''
        This function fixes the EntityName for entities with hex string names by finding another alias to set as the EntityName for the node.
        '''
        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:

                # Fetch entities with hex string names
                logger.info('Fetching entities with hex string names')
                fetch_query = '''
                    SELECT NodeID, EntityName
                    FROM Lightning_Entities
                    WHERE 
                        EntityName REGEXP '^[0-9a-fA-F]+$'
                '''
                db_cursor.execute(fetch_query)
                hex_entities = db_cursor.fetchall()


                for node_id, entity_name in hex_entities:
                    # Find another alias for the node
                    alias_query = '''
                        SELECT Alias
                        FROM Lightning_NodeAliases
                        WHERE NodeID = %s AND Alias != %s AND Alias NOT REGEXP '^[0-9a-fA-F]+$'
                        ORDER BY lastSeen DESC
                        LIMIT 1
                    '''
                    db_cursor.execute(alias_query, (node_id, entity_name))
                    alias_result = db_cursor.fetchone()

                    if alias_result:
                        new_alias = alias_result[0]
                        # Update the EntityName with the new alias
                        logger.info(f'Updating EntityName for NodeID: {node_id} from {entity_name} to {new_alias}')
                        update_query = '''
                            UPDATE Lightning_Entities
                            SET EntityName = %s
                            WHERE NodeID = %s
                        '''
                        db_cursor.execute(update_query, (new_alias, node_id))

                db_conn.commit()






    def test_functionality(self):

        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:

                db_cursor.execute('SELECT * FROM Lightning_Entities')
                entities = db_cursor.fetchall()
                for entity in entities:
                    print(entity)

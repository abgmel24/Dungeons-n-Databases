'''
This code does not work without:
1. Inserting key for Flask (Line 11 in app.py)
2. Inserting MySQL authentication details (Line 5-7 in db_operations.py)
'''
import mysql.connector
# from helper import helper

class db_operations():
    # constructor with connection path to DB
    def __init__(self, connection = mysql.connector.connect(host="localhost",   # INSERT
                                                            user="root",        # AUTHENTICATION
                                                            password="password")):  # DETAILS
        self.connection = connection
        self.cursor = self.connection.cursor()

        self.cursor.execute('CREATE DATABASE IF NOT EXISTS dmdatabase')

        # No need to close the connection here
        print("Database created or already exists.")
        
        # Reconnect to the database
        self.connection.database = 'dmdatabase'  # This sets the active database
        print("connection made..")

        self.cursor.execute(
        '''
            CREATE OR REPLACE VIEW campaign_stats AS
            SELECT 
                dm.dmID,
                campaign.campaignID, 
                campaign.name, 
                COUNT(p.playerID) AS totalPlayers,
                SUM(p.player_gold) + SUM(it.item_cost) AS partyWealth,
                AVG(p.player_level) AS avgLevel,
                AVG(p.player_expTotal) AS avgExp,
                COUNT(E.encounterID) AS totalEncounters, 
                AVG(E.encounter_rating) AS avgDifficulty, 
                COUNT(M.monsterID) AS totalMonsterSpecies, 
                AVG(M.monster_rating) AS avgChallengeRating, 
                COUNT(N.npcID) AS totalNPCs
            FROM campaign
            INNER JOIN dm ON dm.dmID = campaign.dmID 
            INNER JOIN player p ON campaign.campaignID = p.campaignID
            INNER JOIN Inventory i ON p.playerID = i.playerID
            INNER JOIN Items it ON i.itemID = it.itemID
            INNER JOIN Encounter E ON campaign.campaignID = E.campaignID
            INNER JOIN Encounter_Tracker ET ON E.encounterID = ET.encounterID
            INNER JOIN Monster M ON M.monsterID = ET.monsterID
            INNER JOIN NPC N ON campaign.campaignID = N.campaignID
            GROUP BY dm.dmID, campaign.campaignID, campaign.name
            ORDER BY dm.dmID, campaign.campaignID;
        ''')

    # function to simply execute a DDL or DML query.
    # commits query, returns no results. 
    # best used for insert/update/delete queries with no parameters
    def modify_query(self, query):
        self.cursor.execute(query)
        self.connection.commit()

    # function to simply execute a DDL or DML query with parameters
    # commits query, returns no results. 
    # best used for insert/update/delete queries with named placeholders
    def modify_query_params(self, query, params):
        self.cursor.execute(query, tuple(params))
        self.connection.commit()

    # function to simply execute a DQL query
    # does not commit, returns results
    # best used for select queries with no parameters
    def select_query(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    # function to simply execute a DQL query with parameters
    # does not commit, returns results
    # best used for select queries with named placeholders
    def select_query_params(self, query, params):
        self.cursor.execute(query, tuple(params))
        return self.cursor.fetchall()

    # function to return the value of the first row's 
    # first attribute of some select query.
    # best used for querying a single aggregate select 
    # query with no parameters
    def single_record(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]
    
    # function to return the value of the first row's 
    # first attribute of some select query.
    # best used for querying a single aggregate select 
    # query with named placeholders
    def single_record_params(self, query, params):
        self.cursor.execute(query, tuple(params))
        return self.cursor.fetchone()[0]
    
    # function to return a single attribute for all records 
    # from some table.
    # best used for select statements with no parameters
    def single_attribute(self, query):
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        results = [i[0] for i in results]
        results.remove(None)
        return results
    
    # function to return a single attribute for all records 
    # from some table.
    # best used for select statements with named placeholders
    def single_attribute_params(self, query, params):
        self.cursor.execute(query, tuple(params))
        results = self.cursor.fetchall()
        results = [i[0] for i in results]
        return results
    
    # function for bulk inserting records
    # best used for inserting many records with parameters
    def bulk_insert(self, query, data):
        self.cursor.executemany(query, data)
        self.connection.commit()

    # destructor that closes connection with DB
    def destructor(self):
        self.cursor.close()
        self.connection.close()

    # Runs queries as a transaction
    def transaction_query(self, queries_with_params):
        print(queries_with_params)
        for thing in queries_with_params:
            print(thing)
        try:
            for query, params in queries_with_params:
                self.cursor.execute(query, tuple(params))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            print(f'Error during transaction: {e}')
            raise Exception(f'Transaction failed: {e}') from e
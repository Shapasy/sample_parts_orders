import configparser
import sqlite3

SAMPLE_PARTS_TABLE = \
'''
CREATE TABLE IF NOT EXISTS SamplePart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
'''

MATERIAL_TABLE = \
'''
CREATE TABLE IF NOT EXISTS Material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
'''

PART_MATERIAL_COMPATIBILITY = \
'''
CREATE TABLE IF NOT EXISTS PartMaterialCompatibility (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_part_id INTEGER,
    material_id INTEGER,
    FOREIGN KEY (sample_part_id) REFERENCES SamplePart(id),
    FOREIGN KEY (material_id) REFERENCES Material(id)
)
'''

ORDER_TABLE = \
'''
CREATE TABLE IF NOT EXISTS Orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    is_shipped INTEGER DEFAULT 0
)
'''

ORDER_ITEM_TABLE = \
'''
CREATE TABLE IF NOT EXISTS OrderItem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    sample_part_id INTEGER,
    material_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY (order_id) REFERENCES Orders(id),
    FOREIGN KEY (sample_part_id) REFERENCES SamplePart(id),
    FOREIGN KEY (material_id) REFERENCES Material(id)
)
'''

class DatabaseHandler:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.database_name = config['database']['name']
        self.connection = None

    def connect(self):
        try:
            self.connection = sqlite3.connect(f'{self.database_name}.db')
            return self.connection
        except sqlite3.Error as ex:
            raise ConnectionError(f"Failed to connect to database: {ex}")


    def initialization(self):
        self.connect()
        cursor = cursor = self.connection.cursor()

        cursor.execute(SAMPLE_PARTS_TABLE)
        cursor.execute(MATERIAL_TABLE)
        cursor.execute(PART_MATERIAL_COMPATIBILITY)
        cursor.execute(ORDER_TABLE)
        cursor.execute(ORDER_ITEM_TABLE)

        self.connection.commit()
        self.connection.close()

    def insert_sample_part_meterial_combinations(self):
        self.connect()
        cursor = cursor = self.connection.cursor()

        cursor.execute("INSERT INTO SamplePart (name) VALUES ('Sample Part 1')")
        cursor.execute("INSERT INTO SamplePart (name) VALUES ('Sample Part 2')")
        cursor.execute("INSERT INTO SamplePart (name) VALUES ('Sample Part 3')")

        cursor.execute("INSERT INTO Material (name) VALUES ('Material 1')")
        cursor.execute("INSERT INTO Material (name) VALUES ('Material 2')")
        cursor.execute("INSERT INTO Material (name) VALUES ('Material 3')")

        cursor.execute("INSERT INTO PartMaterialCompatibility (sample_part_id, material_id) VALUES (1, 1)")
        cursor.execute("INSERT INTO PartMaterialCompatibility (sample_part_id, material_id) VALUES (1, 2)")

        cursor.execute("INSERT INTO PartMaterialCompatibility (sample_part_id, material_id) VALUES (2, 1)")
        cursor.execute("INSERT INTO PartMaterialCompatibility (sample_part_id, material_id) VALUES (2, 3)")

        cursor.execute("INSERT INTO PartMaterialCompatibility (sample_part_id, material_id) VALUES (3, 2)")

        self.connection.commit()
        self.connection.close()

# if __name__ == "__main__":
#     DatabaseHandler().insert_sample_part_meterial_combinations()

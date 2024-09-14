from database import DatabaseHandler
from rabbit_mq import RabbitMQHandler

class OrderWorker:
    def __init__(self, order_id, db_connection):
        self.order_id = order_id
        self.db_connection = db_connection
        self.db_cursor = db_connection.cursor()

    def print_order_items(self):
        self.db_cursor.execute(
            '''
            SELECT SamplePart.name, Material.name, OrderItem.quantity
            FROM OrderItem
            JOIN SamplePart ON OrderItem.sample_part_id = SamplePart.id
            JOIN Material ON OrderItem.material_id = Material.id
            WHERE OrderItem.order_id = ?
            ''', (self.order_id,)
        )
        order_items = self.db_cursor.fetchall()

        print(f"+ Order with id ''{self.order_id}'' contains the following items:")
        for item in order_items:
            sample_part_name = item[0]
            material_name = item[1]
            quantity = item[2]
            print(f"-- {sample_part_name} (Material: {material_name} , Quantity: {quantity})")

    def mark_order_as_shipped(self):
        self.db_cursor.execute(
            '''
            UPDATE Orders SET is_shipped = 1 WHERE id = ?
            ''', (self.order_id,)
        )
        self.db_connection.commit()

        print(f"+ Order with id ''{self.order_id}'' marked as shipped")

    def process_order(self):
        self.print_order_items()
        self.mark_order_as_shipped()

def process_order_callback(ch, method, _, order_id):
    order_id = order_id.decode("utf-8")

    database_handler = DatabaseHandler()

    try:
        database_handler.connect()

        OrderWorker(order_id, database_handler.connection).process_order()

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as ex:
        print(f"Worker error while processing order with id ''{order_id}''", str(ex))
    finally:
        if database_handler.connection:
            database_handler.connection.close()

if __name__ == "__main__":
    print('+ Order worker is up & running')
    RabbitMQHandler().start_consuming(process_order_callback)

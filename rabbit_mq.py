import configparser
import pika

class RabbitMQHandler:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.url = config['rabbit_mq']['url']
        self.queue_name = config['rabbit_mq']['queue_name']
        self.connection = None

    def connect(self):
        try:
            params = pika.URLParameters(self.url)
            self.connection = pika.BlockingConnection(params)
            return self.connection
        except pika.exceptions.AMQPError as ex:
            raise ConnectionError(f"Failed to connect to RabbitMQ: {ex}")

    def connect_to_queue(self):
        if not self.connection:
            self.connect()
        try:
            channel = self.connection.channel()
            channel.queue_declare(queue=self.queue_name)
            return channel
        except pika.exceptions.AMQPError as ex:
            self.connection.close()
            raise ConnectionError(f"Failed to connect to the queue channel: {ex}")

    def push_message(self, message):
        try:
            channel = self.connect_to_queue()
            channel.basic_publish(exchange='', routing_key=self.queue_name, body=message)
        except pika.exceptions.AMQPError as ex:
            raise ConnectionError(f"Failed to push a message to the queue: {ex}")
        finally:
            self.connection.close()

    def start_consuming(self, callback_method):
        try:
            channel = self.connect_to_queue()
            channel.basic_consume(queue=self.queue_name, on_message_callback=callback_method)
            channel.start_consuming()
        except pika.exceptions.AMQPError as ex:
            raise ConnectionError(f"Failed to start consuming the queue: {ex}")
        finally:
            self.connection.close()

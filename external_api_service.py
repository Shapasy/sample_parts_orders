import configparser

from flask import Flask, request, jsonify

from rabbit_mq import RabbitMQHandler
from database import DatabaseHandler


APP = Flask(__name__)

def message_response_body(message):
    return jsonify({
        "message": message
    })

def errors_response_body(errors_list):
    return jsonify({
        "errors": errors_list
    })

def get_place_order_validation_errors(data):
    customer_name = data.get('customer_name')
    items = data.get('items', [])

    validation_errors = []

    if not customer_name:
        validation_errors.append("'customer_name' is required")
    if not items:
        validation_errors.append("'items' must include atleast one item per order")
    elif len(items) > 10:
        validation_errors.append("'items' must include atmost ten items per order")

    for i,item in enumerate(items):
        if not isinstance(item, dict):
            validation_errors.append(f"Item with index {i+1}, must be object")
        else:
            sample_part_id = item.get('sample_part_id')
            material_id = item.get('material_id')
            quantity = item.get('quantity')
            if not sample_part_id:
                validation_errors.append(f"Item with index {i+1}, missing sample_part_id")
            if not material_id:
                validation_errors.append(f"Item with index {i+1}, missing material_id")
            if not quantity:
                validation_errors.append(f"Item with index {i+1}, missing quantity")

    return validation_errors

@APP.route('/order', methods=['POST'])
def place_order():
    database_handler = DatabaseHandler()
    try:
        data = request.json
        customer_name = data.get('customer_name')
        items = data.get('items')

        validation_errors = get_place_order_validation_errors(data)
        if validation_errors:
            return errors_response_body(validation_errors), 400

        # you can improve the verification error messages,
        # but you will need more database transactions,
        # or add more logic,
        # it is a trade off.
        verification_errors = []

        database_handler.connect()
        db_connection = database_handler.connection
        db_cursor = db_connection.cursor()

        for item in items:
            sample_part_id = item.get('sample_part_id')
            material_id = item.get('material_id')

            db_cursor.execute(
                '''
                SELECT * FROM PartMaterialCompatibility
                WHERE sample_part_id = ? AND material_id = ?
                ''', (sample_part_id, material_id)
            )

            valid_combination = db_cursor.fetchone()
            if not valid_combination:
                verification_errors.append(
                    f"material are not Compatibilitable with sample part with id {sample_part_id}"
                )

        if verification_errors:
            return errors_response_body(verification_errors), 400

        db_cursor.execute(
            '''
            INSERT INTO Orders (customer_name, is_shipped) VALUES (?, ?)
            ''', (customer_name, 0)
        )
        order_id = db_cursor.lastrowid

        for item in items:
            sample_part_id = item['sample_part_id']
            material_id = item['material_id']
            quantity = item['quantity']

            db_cursor.execute(
                '''
                INSERT INTO OrderItem (order_id, sample_part_id, material_id, quantity)
                VALUES (?, ?, ?, ?)
                ''', (order_id, sample_part_id, material_id, quantity)
            )

        db_connection.commit()

        RabbitMQHandler().push_message(str(order_id))

        return message_response_body("Order placed successfully"), 201
    except Exception as ex:
        print("Error while placing order", str(ex))
        return errors_response_body(["Internal server error"]), 500
    finally:
        if database_handler.connection:
            database_handler.connection.close()

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    DatabaseHandler().initialization()
    APP.run(
        host=config['external_api']['host'],
        port=int(config['external_api']['port']),
        debug=bool(config['external_api']['debuging_mode']),
    )

import mysql.connector

cnx = mysql.connector.connect(
    host="mysql.railway.internal",
    user="root",
    password="YOUR_PASSWORD",
    database="railway"
)

# -------------------------
# INSERT ORDER ITEM
# -------------------------
def insert_order_item(food_item, quantity, order_id):
    try:
        cursor = cnx.cursor()

        cursor.callproc('insert_order_item', (food_item, quantity, order_id))

        cnx.commit()
        cursor.close()

        return 1

    except mysql.connector.Error as err:
        print("Error:", err)
        cnx.rollback()
        return -1


# -------------------------
# INSERT ORDER TRACKING
# -------------------------
def insert_order_tracking(order_id, status):
    cursor = cnx.cursor()

    query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
    cursor.execute(query, (order_id, status))

    cnx.commit()
    cursor.close()


# -------------------------
# GET TOTAL PRICE (FIXED)
# -------------------------
def get_total_order_price(order_id):
    cursor = cnx.cursor()

    query = """
    SELECT SUM(order_items.price * order_items.quantity)
    FROM order_items
    WHERE order_id = %s
    """

    cursor.execute(query, (order_id,))
    result = cursor.fetchone()[0]

    cursor.close()

    return result if result else 0


# -------------------------
# GET NEXT ORDER ID
# -------------------------
def get_next_order_id():
    cursor = cnx.cursor()

    query = "SELECT MAX(order_id) FROM orders"
    cursor.execute(query)

    result = cursor.fetchone()[0]
    cursor.close()

    return 1 if result is None else result + 1


# -------------------------
# GET ORDER STATUS
# -------------------------
def get_order_status(order_id):
    cursor = cnx.cursor()

    query = "SELECT status FROM order_tracking WHERE order_id = %s"
    cursor.execute(query, (order_id,))

    result = cursor.fetchone()
    cursor.close()

    return result[0] if result else None


# -------------------------
# SAVE ORDER (NEW FIXED FLOW)
# -------------------------
def save_order(order_dict):
    order_id = get_next_order_id()

    cursor = cnx.cursor()
    cursor.execute(
        "INSERT INTO orders (order_id, status) VALUES (%s, %s)",
        (order_id, "in progress")
    )
    cnx.commit()
    cursor.close()

    for item, qty in order_dict.items():
        if insert_order_item(item, qty, order_id) == -1:
            return -1

    insert_order_tracking(order_id, "in progress")

    return order_id
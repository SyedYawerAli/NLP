from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

app = FastAPI()

inprogress_orders = {}


# -------------------------
# MAIN ROUTE
# -------------------------
@app.post("/")
async def handle_request(request: Request):

    payload = await request.json()

    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    session_id = generic_helper.extract_session_id(
        output_contexts[0]["name"]
    )

    intent_map = {
        'add.order': add_to_order,
        'remove.order': remove_from_order,
        'complete.order ongoing-context': complete_order,
        'Track.order-ongoing-context': track_order
    }

    return intent_map[intent](parameters, session_id)


# -------------------------
# ADD ORDER
# -------------------------
def add_to_order(parameters: dict, session_id: str):

    food_items = parameters["food-item"]
    quantities = parameters["number"]

    if len(food_items) != len(quantities):
        return JSONResponse({"fulfillmentText": "Invalid input"})

    new_order = dict(zip(food_items, quantities))

    if session_id in inprogress_orders:
        inprogress_orders[session_id].update(new_order)
    else:
        inprogress_orders[session_id] = new_order

    order_str = generic_helper.get_str_from_food_dict(
        inprogress_orders[session_id]
    )

    return JSONResponse({
        "fulfillmentText": f"So far: {order_str}"
    })


# -------------------------
# COMPLETE ORDER (FIXED)
# -------------------------
def complete_order(parameters: dict, session_id: str):

    if session_id not in inprogress_orders:
        return JSONResponse({
            "fulfillmentText": "No active order found."
        })

    order = inprogress_orders[session_id]

    order_id = db_helper.save_order(order)

    if order_id == -1:
        return JSONResponse({
            "fulfillmentText": "Error placing order."
        })

    total = db_helper.get_total_order_price(order_id)

    del inprogress_orders[session_id]

    return JSONResponse({
        "fulfillmentText": (
            f"🎉 Order placed successfully!\n"
            f"Order ID: {order_id}\n"
            f"Total Price: {total}"
        )
    })


# -------------------------
# TRACK ORDER
# -------------------------
def track_order(parameters: dict, session_id: str):

    order_id = int(parameters['order_id'])

    status = db_helper.get_order_status(order_id)

    if status:
        msg = f"Order {order_id} status: {status}"
    else:
        msg = "Order not found."

    return JSONResponse({"fulfillmentText": msg})
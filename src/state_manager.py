import ujson

# Load ticket and serving numbers from a saved state in a JSON file
def load_state():
    try:
        with open("state.json", "r") as f:
            data = ujson.load(f)
            return data['ticket_number'], data['serving_number']
    except:
        return 0, 0  # Default to 0 if no saved state found

# Save the current ticket and serving numbers to a JSON file
def save_state(ticket_number, serving_number):
    with open("state.json", "w") as f:
        data = {'ticket_number': ticket_number, 'serving_number': serving_number}
        ujson.dump(data, f)

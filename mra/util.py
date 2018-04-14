import json
import json5

def load_json(json_string:str):
    j = None
    try:
        j = json.loads(possible_json)
    except (json.JSONDecodeError, TypeError):
        # don't catch this error if it happens
        j = json5.loads(possible_json)

    return j
from quart import jsonify


def success(data: dict, status: int = 200):
    """
    Create a successful JSON response.

    :param data: The response payload.
    :param status: The HTTP status code.
    :return: A JSON response and status code.
    """
    return jsonify(data), status


def error(data: str, status: int):
    """
    Create an error JSON response.

    :param message: The error message.
    :param status: The HTTP status code.
    :return: A JSON response and status code.
    """
    return jsonify({"error": data}), status
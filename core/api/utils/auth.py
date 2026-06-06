from quart import jsonify, request

from core import cfg


async def apikey_required():
    """
    Authenticate requests using the configured API key.

    :return: An unauthorized response if authentication fails.
    """
    if request.headers.get("X-API-Key") != cfg.API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
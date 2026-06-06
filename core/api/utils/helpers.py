from quart import render_template

async def render_result(
    title: str,
    description: str,
    status: int = 200
):
    """
    Render a result page.

    :param title: The page title.
    :param description: The page description.
    :param status: The HTTP status code.
    :return: The rendered page and status code.
    """
    return await render_template(
        "result.html",
        title=title,
        description=description
    ), status


async def render_error():
    """
    Render the default verification error page.

    :return: The rendered error page and status code.
    """
    return await render_result(
        title="Verification Failed",
        description=(
            "Something went wrong. If this issue persists, "
            "please contact a server Administrator."
        ),
        status=400,
    )
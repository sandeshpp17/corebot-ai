from corebot_ai.api.main import create_app


def test_health_route() -> None:
    app = create_app()
    routes = {route.path for route in app.routes}
    assert "/health" in routes

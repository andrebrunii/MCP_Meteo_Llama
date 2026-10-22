"""Test offline: MCP reale; meteo e modello simulati. Non certifica Ollama."""
import asyncio
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import mcp_weather_test as client
from mcp import StdioServerParameters

WEATHER = {"city": "Roma", "temperature_c": 20.5, "humidity_percent": 62,
           "wind_kmh": 8.0, "condition": "Sereno", "valid_at": "2000-01-01T12:00",
           "timezone": "Europe/Rome", "source": "Open-Meteo"}


class WeatherTests(unittest.TestCase):
    def test_reject_other_tool(self):
        with self.assertRaises(RuntimeError):
            client.validate_call({"tool_calls": [{"function": {"name": "run_shell", "arguments": {"city": "Roma"}}}]}, "Roma")

    def test_reject_wrong_city(self):
        with self.assertRaises(RuntimeError):
            client.validate_call({"tool_calls": [{"function": {"name": "get_current_weather", "arguments": {"city": "Milano"}}}]}, "Roma")

    def test_missing_call_is_failure(self):
        with self.assertRaises(RuntimeError):
            client.validate_call({"content": "Oggi fa bello"}, "Roma")

    def test_wrong_weather_fails(self):
        final = dict(WEATHER, temperature_c=99)
        self.assertFalse(client.compare(final, WEATHER)["temperature_c"])

    def test_real_mcp_transport_with_mock_model_and_weather(self):
        root = str(Path(__file__).resolve().parent)
        with tempfile.TemporaryDirectory() as tmp:
            runner = Path(tmp) / "fixture_server.py"
            runner.write_text(
                "import sys\nsys.path.insert(0, " + repr(root) + ")\n"
                "import mcp_weather_server as server\n"
                "server.fetch_weather = lambda city: " + repr(WEATHER) + "\n"
                "server.mcp.run(transport='stdio')\n", encoding="utf-8")
            def mocked_ollama(path, payload):
                if path == "/api/show":
                    return {"capabilities": ["tools"]}
                if "tools" in payload:
                    return {"done": True, "done_reason": "stop", "message": {
                        "role": "assistant", "content": "", "tool_calls": [{"function": {
                            "name": "get_current_weather", "arguments": {"city": "Roma"}}}]}}
                return {"done": True, "done_reason": "stop", "message": {
                    "role": "assistant", "content": json.dumps(WEATHER)}}
            report = {}
            args = SimpleNamespace(model="MOCK_MODEL", city="Roma", check_tool=False)
            params = StdioServerParameters(command=sys.executable, args=[str(runner)])
            with patch.object(client, "StdioServerParameters", return_value=params), patch.object(client, "ollama", side_effect=mocked_ollama), redirect_stdout(io.StringIO()):
                asyncio.run(client.experiment(args, report))
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["weather"], WEATHER)
            self.assertEqual(report["tool_call"]["name"], "get_current_weather")
            self.assertTrue(all(report["checks"].values()))


if __name__ == "__main__":
    unittest.main()

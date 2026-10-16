import pytest
from backend.services.sandbox_service import SandboxService

def test_safe_execution():
    res = SandboxService.execute_test_case("python", "print(10 + 25)", "")
    assert res["status"] == "PASSED"
    assert res["stdout"].strip() == "35"

def test_hostile_os_block():
    res = SandboxService.execute_test_case("python", "import os\nprint(os.getcwd())", "")
    assert res["status"] == "SECURITY_BLOCKED"
    assert "strictly prohibited" in res["stderr"]

def test_hostile_socket_block():
    res = SandboxService.execute_test_case("python", "import socket\ns = socket.socket()", "")
    assert res["status"] == "SECURITY_BLOCKED"
    assert "strictly prohibited" in res["stderr"]

def test_timeout_termination():
    res = SandboxService.execute_test_case("python", "while True:\n    pass", "", timeout=1.0)
    assert res["status"] == "TIMEOUT"
    assert "exceeded" in res["stderr"]

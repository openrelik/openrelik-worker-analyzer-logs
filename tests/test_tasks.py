# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import filecmp
import json
from unittest.mock import patch

from fakeredis import TcpFakeServer
from threading import Thread

from src.tasks import run_ssh_analyzer

import contextlib
import redis
import time

_INPUT_FILES = [
    {
        "id": 1,
        "uuid": "445027ec76ef42f8a463fdbaf162d2b7",
        "display_name": "secure",
        "extension": "",
        "data_type": "file:generic",
        "path": "test_data/secure",
    }
]

_INPUT_FILES_SSH_EVENTS_NO_BRUTEFORCE = [
    {
        "id": 1,
        "uuid": "445027ec76ef42f8a463fdbaf162d2b9",
        "display_name": "secure.1",
        "extension": "",
        "data_type": "file:generic",
        "path": "test_data/secure.1",
    }
]

_INPUT_FILES_WITHOUT_SSH_EVENTS = [
    {
        "id": 1,
        "uuid": "445027ec76ef42f8a463fdbaf162d2b8",
        "display_name": "shadow",
        "extension": "",
        "data_type": "file:generic",
        "path": "test_data/shadow",
    }
]


# @contextlib.contextmanager
# def run_fake_server(server_address):
server_address = ("127.0.0.1", 6379)
server = TcpFakeServer(server_address, server_type="redis")
server_thread = Thread(target=server.serve_forever, daemon=True)
server_thread.daemon = True
server_thread.start()
# Wait for the server thread to start
time.sleep(0.1)
# try:
#     # Yield the server or a client connection
#     yield redis.Redis(host=server_address[0], port=server_address[1])
# finally:
#     server.shutdown()
#     server.server_close()
#     server_thread.join()


class TestTasks:
    @patch("src.app.redis.Redis.from_url")
    def test_run_ssh_analyzer(self, mock_redisclient):
        """Test LinuxSSHAnalysis task run."""
        # with run_fake_server(self.server_address) as redis_client:
        # Configure the mock to return the connected fake redis client
        # mock_redisclient.return_value = redis_client

        output = run_ssh_analyzer(
            input_files=_INPUT_FILES,
            output_path="/tmp",
            workflow_id="deadbeef",
            task_config={},
        )

        output_dict = json.loads(base64.b64decode(output))
        output_path = output_dict.get("output_files")[0].get("path")
        assert filecmp.cmp(
            output_path, "test_data/linux_ssh_analysis.md", shallow=False
        )

    @patch("src.app.redis.Redis.from_url")
    def test_task_report_no_ssh_events(self, mock_redisclient):
        """Test for proper task report summary."""
        # with run_fake_server(self.server_address) as redis_client:
        #     # Configure the mock to return the connected fake redis client
        #     mock_redisclient.return_value = redis_client

        output = run_ssh_analyzer(
            input_files=_INPUT_FILES_WITHOUT_SSH_EVENTS,
            output_path="/tmp",
            workflow_id="deadbeef",
            task_config={},
        )

        output_dict = json.loads(base64.b64decode(output))
        output_task_report_summary = output_dict.get("task_report").get("content")
        assert (
            "No SSH authentication events in input files." in output_task_report_summary
        )

    @patch("src.app.redis.Redis.from_url")
    def test_task_report_no_bruteforce(self, mock_redisclient):
        """Test for proper task report summary."""
        # with run_fake_server(self.server_address) as redis_client:
        #     # Configure the mock to return the connected fake redis client
        #     mock_redisclient.return_value = redis_client

        output = run_ssh_analyzer(
            input_files=_INPUT_FILES_SSH_EVENTS_NO_BRUTEFORCE,
            output_path="/tmp",
            workflow_id="deadbeef",
            task_config={},
        )

        output_dict = json.loads(base64.b64decode(output))
        output_task_report_summary = output_dict.get("task_report").get("content")
        assert "No findings for brute force analysis" in output_task_report_summary

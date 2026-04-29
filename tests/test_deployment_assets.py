# Copyright 2026 Jiacheng Ni
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class DeploymentAssetTests(unittest.TestCase):
    def test_deploy_refuses_dirty_archive_and_runs_bootstrap(self) -> None:
        deploy = read("scripts/deploy_server.ps1")

        self.assertIn("git -C $repo status --porcelain", deploy)
        self.assertIn("Refusing to deploy a dirty worktree", deploy)
        self.assertIn("git -C $repo archive", deploy)
        self.assertIn("APP_ROOT=\"$remote_root\" bash scripts/bootstrap_server.sh", deploy)
        self.assertIn("scripts/configure_nginx_ai.sh", deploy)
        self.assertIn("openclaw channels login --channel openclaw-weixin", deploy)

    def test_bootstrap_installs_weixin_and_backs_up_workspace(self) -> None:
        bootstrap = read("scripts/bootstrap_server.sh")

        self.assertIn('openclaw plugins install "@tencent-weixin/openclaw-weixin"', bootstrap)
        self.assertIn("openclaw config set plugins.entries.openclaw-weixin.enabled true", bootstrap)
        self.assertIn('cp -a "$OPENCLAW_HOME/workspace"', bootstrap)
        self.assertIn(".yoloong-managed", bootstrap)
        self.assertIn("openclaw-gateway.service", bootstrap)

    def test_nginx_proxy_script_is_idempotent_and_verifies_config(self) -> None:
        nginx = read("scripts/configure_nginx_ai.sh")

        self.assertIn("location /ai/", nginx)
        self.assertIn("proxy_pass $UPSTREAM", nginx)
        self.assertIn("include {snippet_path}", nginx)
        self.assertIn("nginx -t", nginx)
        self.assertIn("systemctl reload nginx", nginx)

    def test_openclaw_gateway_service_uses_path_lookup_and_loopback(self) -> None:
        service = read("systemd/openclaw-gateway.service")

        self.assertIn("ExecStart=/usr/bin/env openclaw gateway run", service)
        self.assertIn("--bind loopback", service)
        self.assertIn("--port 18789", service)


if __name__ == "__main__":
    unittest.main()

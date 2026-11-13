"""Offline tests for the peer-relay inbox host adapters.

Run: python3 -m unittest discover -s modules/peer-relay/tests -v

No network: the Bitbucket HTTP call is replaced by a fake (`inbox.HTTP_GET`), and the
git repositories are throwaway ones under a temporary directory.
"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.join(HERE, "..", "skills", "peer-relay", "inbox.py")
spec = importlib.util.spec_from_file_location("inbox", INBOX)
inbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inbox)

API = inbox.BB_API


def git_repo(remote_url):
    d = tempfile.mkdtemp()
    subprocess.run(["git", "init", "-q", d], check=True)
    subprocess.run(["git", "-C", d, "remote", "add", "origin", remote_url], check=True)
    return d


class FakeHTTP:
    """Maps a URL prefix to (status, body). Records every URL it was asked for."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, url, token):
        self.calls.append(url)
        assert token == "tok", "the token must reach the HTTP layer unchanged"
        for prefix, answer in self.routes:
            if url.startswith(prefix):
                return answer
        return 404, {}


class BitbucketRepoUrl(unittest.TestCase):
    def test_ssh_and_https_forms(self):
        for url in ("git@bitbucket.org:acme/widgets.git",
                    "git@ssh.bitbucket.org:acme/widgets.git",
                    "ssh://git@ssh.bitbucket.org/acme/widgets.git",
                    "https://bitbucket.org/acme/widgets",
                    "https://someone@bitbucket.org/acme/widgets.git"):
            self.assertEqual(inbox.bitbucket_repo(url), ("acme", "widgets"), url)

    def test_non_bitbucket_url_is_an_error(self):
        with self.assertRaises(inbox.HostError):
            inbox.bitbucket_repo("https://github.com/acme/widgets.git")


class DetectHost(unittest.TestCase):
    def test_auto_follows_the_remote(self):
        self.assertEqual(inbox.detect_host(git_repo("git@ssh.bitbucket.org:acme/w.git"), "origin", "auto"),
                         "bitbucket")
        self.assertEqual(inbox.detect_host(git_repo("https://github.com/acme/w.git"), "origin", "auto"),
                         "github")

    def test_forced_wins(self):
        self.assertEqual(inbox.detect_host(git_repo("https://github.com/acme/w.git"), "origin", "bitbucket"),
                         "bitbucket")


class Pagination(unittest.TestCase):
    def tearDown(self):
        inbox.HTTP_GET = inbox.http_get_json

    def test_follows_next_and_checks_size(self):
        inbox.HTTP_GET = FakeHTTP([
            ("https://x/p2", (200, {"values": [3], "size": 3})),
            ("https://x/p1", (200, {"values": [1, 2], "size": 3, "next": "https://x/p2"})),
        ])
        self.assertEqual(inbox.bb_paginate("https://x/p1", "tok"), [1, 2, 3])

    def test_short_read_is_an_error_not_a_smaller_answer(self):
        inbox.HTTP_GET = FakeHTTP([("https://x/p1", (200, {"values": [1, 2], "size": 5}))])
        with self.assertRaises(inbox.HostError):
            inbox.bb_paginate("https://x/p1", "tok")

    def test_404_names_both_causes(self):
        inbox.HTTP_GET = FakeHTTP([])
        with self.assertRaises(inbox.HostError) as ctx:
            inbox.bb_get("https://x/missing", "tok")
        self.assertIn("token invalid OR repository not visible", str(ctx.exception))


class ListPrsBitbucket(unittest.TestCase):
    def setUp(self):
        self.root = git_repo("git@ssh.bitbucket.org:acme/widgets.git")
        self.base = f"{API}/repositories/acme/widgets"

    def tearDown(self):
        inbox.HTTP_GET = inbox.http_get_json

    def pr(self, number, state="OPEN", full_name="acme/widgets", branch="docs/2026-01-01_x__relay"):
        return {"id": number, "state": state,
                "source": {"branch": {"name": branch}, "repository": {"full_name": full_name}}}

    def test_open_only_removed_excluded_and_fetch_ref(self):
        inbox.HTTP_GET = FakeHTTP([
            (f"{self.base}/pullrequests/7/diffstat", (200, {"size": 2, "values": [
                {"status": "added", "new": {"path": "acme_wiki/work/relay/2026-01-01_x.md"}},
                {"status": "removed", "old": {"path": "acme_wiki/work/relay/old.md"}, "new": None},
            ]})),
            (f"{self.base}/pullrequests?", (200, {"size": 2, "values": [
                self.pr(7), self.pr(8, state="MERGED"),
            ]})),
        ])
        prs = inbox.list_prs_bitbucket(self.root, "origin", "main", None, "tok")
        self.assertEqual(len(prs), 1, "a non-OPEN PR returned by the query must be filtered out")
        self.assertEqual(prs[0]["number"], 7)
        self.assertEqual(prs[0]["files"], [{"path": "acme_wiki/work/relay/2026-01-01_x.md"}])
        self.assertEqual(prs[0]["fetchRef"], "refs/heads/docs/2026-01-01_x__relay")

    def test_pr_from_a_fork_is_not_silently_skipped(self):
        inbox.HTTP_GET = FakeHTTP([
            (f"{self.base}/pullrequests?", (200, {"size": 1, "values": [self.pr(9, full_name="other/widgets")]})),
        ])
        with self.assertRaises(inbox.HostError):
            inbox.list_prs_bitbucket(self.root, "origin", "main", None, "tok")

    def test_single_pr_mode_reads_any_state(self):
        inbox.HTTP_GET = FakeHTTP([
            (f"{self.base}/pullrequests/5/diffstat", (200, {"size": 0, "values": []})),
            (f"{self.base}/pullrequests/5", (200, self.pr(5, state="MERGED"))),
        ])
        prs = inbox.list_prs_bitbucket(self.root, "origin", "main", 5, "tok")
        self.assertEqual([p["number"] for p in prs], [5])


class GithubContract(unittest.TestCase):
    def test_fetch_ref_is_the_pull_head(self):
        calls = []

        def fake_run(cmd, root):
            calls.append(cmd)
            return '[{"number": 12, "headRefName": "docs/a__relay", "files": []}]'

        real = inbox.run
        inbox.run = fake_run
        try:
            prs = inbox.list_prs_github(".", "main", None)
        finally:
            inbox.run = real
        self.assertEqual(prs[0]["fetchRef"], "pull/12/head")
        self.assertEqual(calls[0][:3], ["gh", "pr", "list"])


class Registry(unittest.TestCase):
    PEERS = ("---\nself: acme\nhost_token_cmd: {cmd}\n---\n# Peers\n## `other`\n")

    def setUp(self):
        self.saved = os.environ.pop("PEER_RELAY_TOKEN", None)

    def tearDown(self):
        os.environ.pop("PEER_RELAY_TOKEN", None)
        if self.saved is not None:
            os.environ["PEER_RELAY_TOKEN"] = self.saved

    def test_resolve_self_from_frontmatter(self):
        self.assertEqual(inbox.resolve_self(None, self.PEERS.format(cmd="x"), "acme_wiki"), "acme")

    def test_token_from_command_without_a_shell(self):
        # A command with inner quotes goes inside YAML single quotes ('' escapes a quote):
        # unquoted, the shared frontmatter parser strips trailing quote characters.
        text = self.PEERS.format(cmd=f"'{sys.executable} -c \"print(''tok'')\"'")
        self.assertEqual(inbox.token_from_registry(text), "tok")

    def test_plain_command_without_quotes(self):
        script = os.path.join(tempfile.mkdtemp(), "tok.py")
        with open(script, "w") as f:
            f.write("print('tok')\n")
        self.assertEqual(inbox.token_from_registry(self.PEERS.format(cmd=f"{sys.executable} {script}")), "tok")

    def test_env_overrides_the_command(self):
        os.environ["PEER_RELAY_TOKEN"] = "from-env"
        self.assertEqual(inbox.token_from_registry(self.PEERS.format(cmd="false")), "from-env")

    def test_failing_command_is_an_error(self):
        with self.assertRaises(inbox.HostError):
            inbox.token_from_registry(self.PEERS.format(cmd="false"))

    def test_no_token_configured_means_not_checked(self):
        root = git_repo("git@ssh.bitbucket.org:acme/widgets.git")
        found, odd, reason = inbox.open_pr_messages(
            root, "origin", "main", "acme_wiki/work/relay/", "other", "acme", None,
            "bitbucket", "---\nself: acme\n---\n")
        self.assertIsNone(found)
        self.assertIn("token not configured", reason)


if __name__ == "__main__":
    unittest.main()

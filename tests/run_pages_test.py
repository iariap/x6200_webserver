#!/usr/bin/env python3
"""Page tests for the web configurator without the radio.

Starts the real app against a copy of the firmware's default params database and
requests every page, checking the status code and a marker string. Pages that
depend on subsystems not in the image yet (remote-control socket, DX cluster
config, Field Ops helper) must still render.

Usage: tests/run_pages_test.py [db-path]

SPDX-License-Identifier: GPL-2.0-or-later
"""

import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get("PORT", "8099"))

PAGES = [
    ("/", "configurator"),
    ("/bands", "band"),
    ("/digital_modes", "digital"),
    ("/memories", "memor"),
    ("/cw_messages", "message"),
    ("/api/channels", "channels"),
    ("/cluster", "cluster"),
    ("/wfview", "wfview"),
    ("/field", "field"),
    ("/logs", "log"),
    ("/files/", "file"),
    ("/gallery", "galler"),
    ("/backup", "backup"),
    ("/time", "time"),
    ("/remote", "emote"),
    ("/api/bands", "start_freq"),
    ("/api/digital_modes", "freq"),
    ("/api/wfview", "enabled"),
    ("/static/css/base.css", None),
]


def get(path):
    url = f"http://127.0.0.1:{PORT}{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:                                  # connection refused, timeout...
        return 0, str(e)


def main():
    db = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "tests", "params.default.db")
    if not os.path.exists(db):
        print(f"falta la base de datos: {db}")
        return 2

    work = tempfile.mkdtemp(prefix="webserver-test-")

    # PyPI's bottle-sqlite 0.2.0 still calls inspect.getargspec, which Python
    # 3.11 removed. Buildroot patches it (0001-Add-python3.11-support.patch) so
    # the image is fine; this keeps the test working with the released wheel.
    with open(os.path.join(work, "sitecustomize.py"), "w") as f:
        f.write(
            "import collections, inspect\n"
            "if not hasattr(inspect, 'getargspec'):\n"
            "    _ArgSpec = collections.namedtuple('ArgSpec', 'args varargs keywords defaults')\n"
            "    def _getargspec(func):\n"
            "        s = inspect.getfullargspec(func)\n"
            "        return _ArgSpec(s.args, s.varargs, s.varkw, s.defaults)\n"
            "    inspect.getargspec = _getargspec\n"
        )

    env = dict(os.environ, PYTHONPATH=os.pathsep.join([work, os.path.join(DIR, "src")]))
    proc = subprocess.Popen(
        [sys.executable, "-m", "x6100_webserver", "--db", db, "--host", "127.0.0.1",
         "--port", str(PORT), "--https-port", "0", "--filebrowser-path", work],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )

    try:
        for _ in range(60):
            if get("/")[0] == 200:
                break
            time.sleep(0.2)

        print("== paginas del web configurator ==")
        checks = fails = 0
        for path, marker in PAGES:
            checks += 1
            status, body = get(path)

            if status != 200:
                print(f"  FALLO {path:<18} HTTP {status}")
                fails += 1
            elif marker and marker not in body.lower():
                print(f"  FALLO {path:<18} sin \"{marker}\"")
                fails += 1
            else:
                print(f"  ok    {path:<18} {len(body)} bytes")

        print(f"\n{checks} comprobaciones, {fails} fallos")

        if fails:
            proc.terminate()
            out = proc.communicate(timeout=5)[0]
            print("\n--- log del servidor ---")
            print("\n".join(out.splitlines()[-30:]))
            return 1
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())

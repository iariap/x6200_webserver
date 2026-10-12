# X6200 web configurator

The web configurator that runs on the Xiegu **X6200** alternative firmware
([iariap/x6200_gui](https://github.com/iariap/x6200_gui)), as a standalone
Python app.

It is a port of the web configurator that ships with **IU1WXY's X6100 firmware**
(`webserver/` in [IU1WXY/X6100-IU1WXY](https://github.com/IU1WXY/X6100-IU1WXY)),
which in turn is an extended fork of Georgy Dyuldin's `x6100_webserver`.
Upstream is GPL-2.0-or-later (see `LICENSE`).

## What changed for the X6200

- User-facing identity: titles, footer, login/backup/log-export names, the
  self-signed certificate subject (`CN=x6200`, `DNS:x6200`) and the default
  wfview credentials (`x6200`).
- `/tmp/x6200_remote.sock` for the live remote-control socket, and
  `x6200-field` (+ `X6200_FIELD_DIR`/`X6200_CALL`) for the Field Ops helper.
- The Python package keeps the upstream name `x6100_webserver` (module, console
  script and systemd/init integration) to stay compatible with the image.

## Pages

Band editor, digital modes, memories and channels, CW messages, DX cluster,
wfview server, Field Ops, logs (ADIF export), file browser, gallery, backup and
restore, time/NTP, remote control, plus the JSON API under `/api`.

Pages whose subsystem may not be running yet (the live remote control socket, the
DX cluster, the Field Ops helper) still render; they show an empty or disabled state
instead of failing. All of them are in the ROM now - the remote socket is served by
the GUI, the cluster by its own app and the Field Ops helper by
`/usr/sbin/x6200-field` - so the pages show live data when they are up.

## Running it on a PC

```sh
pip install bottle bottle-sqlite
PYTHONPATH=src python3 -m x6100_webserver \
    --db tests/params.default.db --host 127.0.0.1 --port 8080 --https-port 0 \
    --filebrowser-path /tmp
python3 tests/run_pages_test.py      # checks every page renders
```

`tests/params.default.db` is the default database the firmware ships
(`/usr/share/x6200/params.default.db`); regenerate it with the `sql/` files of
the firmware if the schema changes.

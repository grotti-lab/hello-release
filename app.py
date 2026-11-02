"""hello-release — yggdrasil hosting's test of grotti-release (D-049, D-050): a page, a health check, and /probe, which
reports what the release's sandbox lets it do."""
import getpass
import json
import os
import pathlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ["PORT"])
DATA = pathlib.Path(os.environ["DATA_DIR"])
VERSION = pathlib.Path("VERSION").read_text().strip()
BUILT = pathlib.Path("BUILT").read_text().strip() if pathlib.Path("BUILT").exists() else "no build"
starts = DATA / "starts"
START = int(starts.read_text()) + 1 if starts.exists() else 1
starts.write_text(str(START))


def can(f):
    try:
        f()
        return True
    except Exception:
        return False


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        kind = "text/plain"
        if self.path == "/healthz":
            body = "ok"
        elif self.path == "/probe":
            kind = "application/json"
            body = json.dumps({
                "user": getpass.getuser(), "version": VERSION, "built": BUILT, "start": START,
                "write_data_dir": can(lambda: (DATA / "probe").write_text("x")),
                "write_its_code": can(lambda: pathlib.Path("probe").write_text("x")),
                "write_tmp": can(lambda: pathlib.Path("/tmp/probe").write_text("x")),
                "read_grotti_secrets": can(lambda: open("/etc/grotti/grotti.env").read()),
                "list_home": can(lambda: os.listdir("/home")),
                "write_usr_local": can(lambda: pathlib.Path("/usr/local/probe").write_text("x")),
            })
        else:
            body = f"hello from release {VERSION} ({BUILT}), start #{START}\n"
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

"""Command-line access to the ledger.  python3 -m wrfgate.ledger log KEY=VALUE ...  |  verify"""
import sys
from .common import ledger_append, ledger_verify
if __name__ == "__main__":
    if sys.argv[1] == "verify":
        ok, msg = ledger_verify(); print(("OK   " if ok else "BAD  ") + msg); raise SystemExit(0 if ok else 1)
    ev = dict(a.split("=", 1) for a in sys.argv[2:])
    print(ledger_append(ev))

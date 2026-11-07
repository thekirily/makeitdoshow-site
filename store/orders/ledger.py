"""The order ledger: one SQLite file, one row per order, every state change recorded.

Safety comes from the database, not from care:
  * processor_order_id and capture_id are UNIQUE, so one payment can only ever mark one order paid;
  * webhook events are stored under (processor, event_id) PRIMARY KEY, so a re-delivered event is a no-op;
  * every step claims its order with `UPDATE ... WHERE state = <expected>`; only the caller that changed
    exactly one row may continue, so two robots (or a retry racing a webhook) can't both print it.
"""
import json, os, sqlite3, time, secrets
from .common import STORE, log_event

DB_PATH = os.environ.get('ORDER_DB', os.path.join(STORE, 'var', 'orders.sqlite'))

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders(
  id TEXT PRIMARY KEY,
  created REAL NOT NULL,
  state TEXT NOT NULL,
  product TEXT NOT NULL,
  lines TEXT NOT NULL,             -- JSON [{year, name}]
  total_cents INTEGER NOT NULL,
  currency TEXT NOT NULL,
  processor TEXT,
  processor_order_id TEXT UNIQUE,
  capture_id TEXT UNIQUE,
  paid_cents INTEGER,
  ship TEXT,                       -- JSON shipping address from the processor
  email TEXT,
  lulu_job_id TEXT,
  lulu_status TEXT,
  note TEXT,
  updated REAL
);
CREATE TABLE IF NOT EXISTS events(
  processor TEXT NOT NULL, event_id TEXT NOT NULL, received REAL NOT NULL, outcome TEXT,
  PRIMARY KEY(processor, event_id)
);
CREATE TABLE IF NOT EXISTS files(
  order_id TEXT NOT NULL, line_no INTEGER NOT NULL, kind TEXT NOT NULL, path TEXT, sha256 TEXT,
  url TEXT, validation_id TEXT, validation_status TEXT, detail TEXT,
  PRIMARY KEY(order_id, line_no, kind)
);
CREATE TABLE IF NOT EXISTS transitions(
  order_id TEXT NOT NULL, at REAL NOT NULL, frm TEXT, too TEXT, why TEXT
);
"""

# The only states from which printing may start. Anything else is not paid, not verified, or already handled.
PRINTABLE = 'paid'


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH, isolation_level=None, timeout=30)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c


def new_order(product, lines, total_cents, currency='USD'):
    oid = 'MID-' + time.strftime('%y%m%d') + '-' + secrets.token_hex(4).upper()
    with connect() as c:
        c.execute('INSERT INTO orders(id, created, state, product, lines, total_cents, currency, updated) VALUES(?,?,?,?,?,?,?,?)',
                  (oid, time.time(), 'created', product, json.dumps(lines), total_cents, currency, time.time()))
        c.execute('INSERT INTO transitions VALUES(?,?,?,?,?)', (oid, time.time(), None, 'created', 'checkout form accepted'))
    log_event('order.created', order_id=oid, product=product, lines=lines, total_cents=total_cents)
    return oid


def get(oid):
    with connect() as c:
        r = c.execute('SELECT * FROM orders WHERE id=?', (oid,)).fetchone()
    return dict(r) if r else None


def by_processor_order(proc_order_id):
    with connect() as c:
        r = c.execute('SELECT * FROM orders WHERE processor_order_id=?', (proc_order_id,)).fetchone()
    return dict(r) if r else None


def move(oid, frm, to, why, **fields):
    """Atomic compare-and-set. Returns True only if this caller moved the order from `frm` to `to`."""
    frm_list = [frm] if isinstance(frm, str) else list(frm)
    sets = ', '.join([f'{k}=?' for k in fields] + ['state=?', 'updated=?'])
    q = f'UPDATE orders SET {sets} WHERE id=? AND state IN ({",".join("?" * len(frm_list))})'
    args = [*(json.dumps(v) if isinstance(v, (dict, list)) else v for v in fields.values()), to, time.time(), oid, *frm_list]
    with connect() as c:
        try:
            n = c.execute(q, args).rowcount
        except sqlite3.IntegrityError as e:  # e.g. the same capture id already marked another order paid
            log_event('order.refused', order_id=oid, frm=frm_list, to=to, why=f'integrity: {e}')
            return False
        if n == 1:
            c.execute('INSERT INTO transitions VALUES(?,?,?,?,?)', (oid, time.time(), ','.join(frm_list), to, why))
    log_event('order.move' if n == 1 else 'order.move_refused', order_id=oid, frm=frm_list, to=to, why=why,
              **{k: v for k, v in fields.items() if k not in ('ship',)})
    return n == 1


def seen_event(processor, event_id, outcome):
    """Record a webhook event; returns False if it was already recorded (a re-delivery)."""
    with connect() as c:
        try:
            c.execute('INSERT INTO events VALUES(?,?,?,?)', (processor, event_id, time.time(), outcome))
            return True
        except sqlite3.IntegrityError:
            return False


def set_file(oid, line_no, kind, **f):
    with connect() as c:
        c.execute('INSERT INTO files(order_id, line_no, kind) VALUES(?,?,?) ON CONFLICT DO NOTHING', (oid, line_no, kind))
        if f:
            c.execute(f'UPDATE files SET {", ".join(k + "=?" for k in f)} WHERE order_id=? AND line_no=? AND kind=?',
                      [*f.values(), oid, line_no, kind])


def files(oid):
    with connect() as c:
        return [dict(r) for r in c.execute('SELECT * FROM files WHERE order_id=? ORDER BY line_no, kind', (oid,))]


def in_state(state):
    with connect() as c:
        return [dict(r) for r in c.execute('SELECT * FROM orders WHERE state=? ORDER BY created', (state,))]


def history(oid):
    with connect() as c:
        return [dict(r) for r in c.execute('SELECT * FROM transitions WHERE order_id=? ORDER BY at', (oid,))]

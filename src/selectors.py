import datetime

class FrozenSelectorError(Exception):
    pass

class ErrorMarker_:
    __slots__ = ()
    def __repr__(self): return "error"
    def __str__(self): return "error"

class ResponseMarker_:
    __slots__ = ()
    def __repr__(self): return "response root"
    def __str__(self): return "response root"

ErrorMarker = ErrorMarker_()
ResponseMarker = ResponseMarker_()

def _runs(r):
    return ''.join(x["text"] for x in r["runs"])

def _text(r):
    if not isinstance(r, dict):
        return r
    for k in ("simpleText", "content", "contents"):
        if k in r:
            return r[k]
    if "runs" in r:
        return _runs(r)
    return r

def _iso(r):
    dt = datetime.datetime.fromisoformat(r)
    return dt

_MODS = {
    "int":   (("toInt", "to_int", "asInt", "as_int"),           int),
    "hex":   (("toHex", "to_hex", "asHex", "as_hex"),           lambda r: int(r, 16) if isinstance(r, str) else int(r)),
    "float": (("toFloat", "to_float", "asFloat", "as_float"),   float),
    "runs":  (("runs",),                                        _runs),
    "simpleText": (("simpleText", "simple_text"),               lambda r: r["simpleText"]),
    "textMin": (("runsOrSimpleText", "simpleTextOrRuns",
                 "runs_or_simple_text", "simple_text_or_runs"), lambda r: r["simpleText"] if "simpleText" in r else _runs(r)),
    "text":  (("text", "str", "string", "content"),             _text),
    "isoDate":  (("isoDate", "iso_date", "date"),               _iso),
}

_NAME_TO_MOD = {alias: canon for canon, (aliases, _) in _MODS.items() for alias in aliases}
_NAME_TO_MOD.update({canon: canon for canon in _MODS})

class Selector:
    __slots__ = ("client", "path", "modificator", "frozen", "err")

    def __init__(self, client):
        self.client = client
        self.path = [ResponseMarker]
        self.modificator = None
        self.frozen = False
        self.err = None

    def __getitem__(self, key):
        if self.frozen:
            raise FrozenSelectorError("Selector is frozen")
        self.path.append(key)
        return self

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        canon = _NAME_TO_MOD.get(name)
        if canon is None:
            raise AttributeError(f"Unknown selector attribute: {name!r}")
        self.modificator = canon
        self.frozen = True
        return self

    def copy(self):
        new = Selector(self.client)
        new.path = self.path.copy()
        new.modificator = self.modificator
        new.frozen = self.frozen
        new.err = self.err
        return new

    def _fail(self, msg, quiet):
        if quiet:
            self.err = msg
            return None
        raise FrozenSelectorError(msg)

    def apply(self, response, quiet=True):
        self.err = None
        result = response
        prev = self.path[0]
        for key in self.path[1:]:
            if isinstance(result, dict):
                if key not in result:
                    return self._fail(f"Path {key!r} not found at {prev!r}", quiet)
                result = result[key]
            elif isinstance(result, (list, tuple)) and isinstance(key, int):
                try:
                    result = result[key]
                except IndexError:
                    return self._fail(f"Index {key!r} out of range at {prev!r}", quiet)
            else:
                return self._fail(
                    f"Cannot descend into {type(result).__name__} at {prev!r} (key {key!r})",
                    quiet,
                )
            prev = key

        if self.modificator is None:
            return result
        try:
            return _MODS[self.modificator][1](result)
        except (KeyError, TypeError, IndexError, ValueError) as e:
            return self._fail(str(e), quiet)
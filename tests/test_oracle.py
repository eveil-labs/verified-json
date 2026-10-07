"""Synthetic cross-language observations; these tests are not completeness proofs."""
import os
import struct
import subprocess
import unittest

ORACLE = os.environ.get("VJ_ORACLE")

def decode_ast(data):
    offset = 0
    def read(n):
        nonlocal offset
        if n > len(data) - offset:
            raise ValueError("truncated AST")
        result = data[offset:offset + n]
        offset += n
        return result
    def count():
        return struct.unpack("<I", read(4))[0]
    def units():
        n = count()
        if n > (len(data) - offset) // 2:
            raise ValueError("truncated units")
        return list(struct.unpack(f"<{n}H", read(2 * n)))
    def value(depth=0):
        if depth > 128:
            raise ValueError("depth bound")
        tag = read(1)[0]
        if tag == 0: return ("null",)
        if tag == 1: return ("bool", False)
        if tag == 2: return ("bool", True)
        if tag == 3: return ("number", read(count()).decode("ascii"))
        if tag == 4: return ("str", units())
        if tag == 5:
            n = count()
            if n > len(data) - offset: raise ValueError("invalid array count")
            return ("array", [value(depth + 1) for _ in range(n)])
        if tag == 6:
            n = count()
            if n > (len(data) - offset) // 5: raise ValueError("invalid object count")
            return ("object", [(units(), value(depth + 1)) for _ in range(n)])
        raise ValueError("unknown tag")
    result = value()
    if offset != len(data): raise ValueError("trailing AST bytes")
    return result

@unittest.skipUnless(ORACLE, "VJ_ORACLE absent: native oracle checks not run")
class OracleTests(unittest.TestCase):
    def call(self, data, args=()):
        result = subprocess.run([ORACLE, *args], input=data.hex().encode() + b"\n",
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.decode("ascii").splitlines()
        self.assertEqual(len(lines), 1)
        pieces = lines[0].split("\t")
        self.assertEqual(pieces[0], "VJ1")
        if pieces[1] == "ok":
            self.assertEqual(len(pieces), 3)
            return ("ok", decode_ast(bytes.fromhex(pieces[2])))
        if pieces[1] == "json":
            self.assertEqual(len(pieces), 3)
            return ("json", bytes.fromhex(pieces[2]))
        self.assertEqual(pieces[1], "err")
        self.assertEqual(len(pieces), 4)
        offset = int(pieces[3])
        self.assertGreaterEqual(offset, 0)
        self.assertLessEqual(offset, len(data))
        return ("err", pieces[2])

    def test_scalar_and_exact_numbers(self):
        for source, expected in [(b"null", ("null",)), (b"true", ("bool", True)),
                                 (b"false", ("bool", False)), (b"-0", ("number", "-0")),
                                 (b"1.00e+02", ("number", "1.00e+02")),
                                 (b"1e99999", ("number", "1e99999")),
                                 (b" \r\n\t42\t", ("number", "42"))]:
            with self.subTest(source=source): self.assertEqual(self.call(source), ("ok", expected))

    def test_containers_duplicate_keys_and_order(self):
        self.assertEqual(self.call(b'{"b":1,"a":2,"b":3}'), ("ok", ("object", [
            ([98], ("number", "1")), ([97], ("number", "2")), ([98], ("number", "3"))])))
        self.assertEqual(self.call(b'[{},[],null,true,"a"]'), ("ok", ("array", [
            ("object", []), ("array", []), ("null",), ("bool", True), ("str", [97])])))
        self.assertEqual(self.call(b'{"a":0,"\\u0061":1}')[1][1][1][0], [97])

    def test_strings_utf8_escapes_and_surrogates(self):
        for source, units in [(b'""', []), (b'"\\n\\t\\b\\f\\r\\/\\\\\\\""', [10,9,8,12,13,47,92,34]),
                              (b'"\\ud800"', [0xD800]), (b'"\\udfff"', [0xDFFF]),
                              (b'"\\ud83d\\ude00"', [0xD83D,0xDE00]),
                              ('"😀"'.encode(), [0xD83D,0xDE00]),
                              ('"é中"'.encode(), [0xE9,0x4E2D]), (b'"\\u0000"', [0])]:
            with self.subTest(source=source): self.assertEqual(self.call(source), ("ok", ("str", units)))

    def test_invalid_document_grammar(self):
        cases = [b"", b" ", b"tru", b"True", b"NULL", b"+1", b"01", b"-01", b"-", b".1",
                 b"1.", b"1e", b"1e+", b"NaN", b"Infinity", b"null true", b"falsex", b"0 0",
                 b"[1,]", b"[,1]", b"[1 2]", b"{\"a\":}", b"{\"a\":1,}", b"{1:2}",
                 b"[", b"{", b'"', b'"\\q"', b'"\\u12"', b'"\\uZZZZ"', b'"\x00"',
                 b"\xef\xbb\xbfnull", b"null\v", b"//comment\nnull", b"[true]x"]
        for source in cases:
            with self.subTest(source=source): self.assertEqual(self.call(source), ("err", "syntax"))

    def test_invalid_raw_utf8(self):
        for raw in [b"\x80", b"\xc0\xaf", b"\xc2", b"\xe0\x80\x80", b"\xed\xa0\x80",
                    b"\xf0\x80\x80\x80", b"\xf4\x90\x80\x80", b"\xf5\x80\x80\x80",
                    b"\xe2(\xa1", b"\xff"]:
            with self.subTest(raw=raw): self.assertEqual(self.call(b'"' + raw + b'"'), ("err", "utf8"))

    def test_number_and_depth_budget_edges(self):
        self.assertEqual(self.call(b"1" * 4096)[0], "ok")
        self.assertEqual(self.call(b"1" * 4097), ("err", "limit"))
        self.assertEqual(self.call(b"[" * 128 + b"0" + b"]" * 128)[0], "ok")
        self.assertEqual(self.call(b"[" * 129 + b"0" + b"]" * 129), ("err", "limit"))

    def test_node_budget_edges(self):
        # Root + 99,999 scalar children exactly exhausts 100,000.
        self.assertEqual(self.call(b"[" + b",".join([b"0"] * 99999) + b"]")[0], "ok")
        self.assertEqual(self.call(b"[" + b",".join([b"0"] * 100000) + b"]"), ("err", "limit"))

    def test_serializer_observation_roundtrip(self):
        for source in [b"-0", b"1.00e-4000", b'"\\ud800"', '"😀é"'.encode(),
                       b'{"a":0,"a":["\\u0000",true,null]}']:
            with self.subTest(source=source):
                kind, encoded = self.call(source, ("--serialize",))
                self.assertEqual(kind, "json")
                self.assertTrue(all(b < 128 for b in encoded))
                self.assertEqual(self.call(encoded), self.call(source))

    def test_malformed_transport(self):
        for line in [b"0\n", b"gg\n", b"00\n00\n", b"\xff\n", b"0 0\n"]:
            with self.subTest(line=line):
                result = subprocess.run([ORACLE], input=line, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, timeout=10)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"VJ1\terr\ttransport\t0\n")

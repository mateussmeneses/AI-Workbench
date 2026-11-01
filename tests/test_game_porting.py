import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from aiwh.cli import main
from aiwh.areas import recommend
from aiwh.game_porting import assess_game_port, inspect_binary, save_game_plan, validate_game_catalog


class GamePortingTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def binary(self, payload, name="game.bin"):
        path = self.root / name
        path.write_bytes(payload)
        return path

    def test_catalog(self):
        stats = validate_game_catalog()
        self.assertGreaterEqual(stats["platforms"], 12)
        self.assertGreaterEqual(stats["tools"], 8)

    def test_n64_endian_variants_and_spoofed_extension(self):
        for magic in ("80371240", "37804012", "40123780"):
            with self.subTest(magic=magic):
                result = inspect_binary(self.binary(bytes.fromhex(magic) + b"\x00" * 64))
                self.assertEqual(result["platform"], "n64")
        self.assertIsNone(inspect_binary(self.binary(b"fake", "fake.z64"))["platform"])

    def test_psx_xex_wii_gc_and_pe(self):
        self.assertEqual(inspect_binary(self.binary(b"PS-X EXE" + b"\x00" * 64))["platform"], "ps1")
        self.assertEqual(inspect_binary(self.binary(b"XEX2" + b"\x00" * 64))["platform"], "xbox360")
        wii = bytearray(64)
        wii[0x18:0x1c] = bytes.fromhex("5d1c9ea3")
        gc = bytearray(64)
        gc[0x1c:0x20] = bytes.fromhex("c2339f3d")
        self.assertEqual(inspect_binary(self.binary(wii))["platform"], "wii")
        self.assertEqual(inspect_binary(self.binary(gc))["platform"], "gamecube")
        pe = bytearray(256)
        pe[:2] = b"MZ"
        pe[0x3c:0x40] = (0x80).to_bytes(4, "little")
        pe[0x80:0x84] = b"PE\x00\x00"
        pe[0x84:0x86] = (0x8664).to_bytes(2, "little")
        result = inspect_binary(self.binary(pe, "unverified.exe"))
        self.assertEqual(result["platform"], "windows-pc")
        self.assertEqual(result["architecture"], "x86-64")

    def test_elf_machine_not_console_proof(self):
        elf = bytearray(64)
        elf[:6] = b"\x7fELF\x02\x01"
        elf[18:20] = (62).to_bytes(2, "little")
        binary = self.binary(elf)
        evidence = inspect_binary(binary)
        self.assertEqual(evidence["format"], "ELF")
        self.assertEqual(evidence["architecture"], "x86-64")
        self.assertIsNone(evidence["platform"])
        triage = assess_game_port(self.root, binary=binary, goal="native pc port")
        self.assertEqual(triage["track"], "triage")
        self.assertFalse(triage["tools"])
        declared = assess_game_port(self.root, binary=binary, platform="ps4", goal="native pc port")
        self.assertEqual(declared["platform_provenance"], "user-declared")
        self.assertEqual(declared["track"], "compatibility-runtime")
        self.assertIn("shadPS4", [t["name"] for t in declared["tools"]])

    def test_matching_and_static_recomp_use_different_tools(self):
        rom = self.binary(bytes.fromhex("80371240") + b"\x00" * 64)
        matching = assess_game_port(self.root, binary=rom, track="matching-decomp")
        static = assess_game_port(self.root, binary=rom, track="static-recomp")
        self.assertIn("decompdecomp", [x["name"] for x in matching["tools"]])
        self.assertNotIn("N64Recomp", [x["name"] for x in matching["tools"]])
        self.assertIn("N64Recomp", [x["name"] for x in static["tools"]])
        self.assertNotIn("decompdecomp", [x["name"] for x in static["tools"]])

    def test_specialized_static_recompilers(self):
        for platform, tool in (("ps1", "PSXRecomp"), ("ps2", "PS2Recomp"),
                               ("ps3", "ps3recomp"), ("xbox360", "XenonRecomp")):
            with self.subTest(platform=platform):
                result = assess_game_port(self.root, platform=platform, track="static-recomp")
                self.assertIn(tool, [t["name"] for t in result["tools"]])

    def test_conflicting_platform_and_unknown_goal(self):
        with self.assertRaisesRegex(ValueError, "conflicts"):
            assess_game_port(self.root, binary=self.binary(b"XEX2" + b"\x00" * 64), platform="ps2")
        with self.assertRaisesRegex(ValueError, "Unknown platform"):
            assess_game_port(self.root, platform="sega-dreamcast")
        result = assess_game_port(self.root)
        self.assertEqual(result["track"], "triage")
        self.assertEqual(result["tools"], [])

    def test_bounded_read_only(self):
        path = self.binary(bytes.fromhex("80371240") + b"\x00" * (1024 * 1024))
        before = (path.stat().st_mtime_ns, path.stat().st_size)
        result = assess_game_port(self.root, binary=path, track="static-recomp")
        self.assertEqual(result["binary"]["sample_bytes"], 4096)
        self.assertEqual((path.stat().st_mtime_ns, path.stat().st_size), before)
        self.assertNotIn(str(path), json.dumps(result))

    def test_private_handoff_requires_explicit_save(self):
        rom = self.binary(bytes.fromhex("80371240") + b"\x00" * 64)
        report = assess_game_port(self.root, binary=rom, track="static-recomp")
        target = self.root / ".ai-workbench" / "GAME_PORT_PLAN.md"
        self.assertFalse(target.exists())
        written = save_game_plan(self.root, report)
        self.assertEqual(written.resolve(), target.resolve())
        self.assertIn("N64Recomp", target.read_text(encoding="utf-8"))
        self.assertEqual(rom.read_bytes()[:4], bytes.fromhex("80371240"))

    def test_area_integration_and_business_isolation(self):
        plan = recommend(self.root, selected=["game-port", "reverse-engineering"])
        self.assertEqual(plan["game_porting"]["track"], "triage")
        self.assertIn("wb-reverse-engineering", plan["skills"])
        self.assertNotIn("game_porting", recommend(self.root, selected=["marketing"]))

    def test_cli(self):
        rom = self.binary(bytes.fromhex("80371240") + b"\x00" * 64)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["game-port", str(self.root), "--binary", str(rom),
                                   "--track", "static-recomp", "--json"]), 0)
        self.assertEqual(json.loads(out.getvalue())["platform"], "n64")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["game-port", str(self.root), "--platform", "ps4",
                                   "--goal", "Fix Vulkan shader stutter"]), 0)
        self.assertIn("Compatibility runtime", out.getvalue())


if __name__ == "__main__":
    unittest.main()

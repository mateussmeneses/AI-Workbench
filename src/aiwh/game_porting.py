"""Read-only game reverse-engineering / porting intake and tool routing.

Only bounded file headers are inspected. A filename, project title or CPU alone
does not prove a console generation or an achievable native port.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .workbench import CAPABILITIES

CATALOG_PATH = CAPABILITIES / "game-porting" / "catalog.json"
HEADER_BYTES = 4096
TRACKS = ("auto", "matching-decomp", "static-recomp", "compatibility-runtime", "triage")
# A verified container may be declared as a newer member of the same family.
COMPATIBLE_DECLARATIONS = {"switch": {"switch2"}}
GAME_AREAS = frozenset(("game-port", "reverse-engineering", "decompilation",
                        "recompilation", "game-modding"))


def game_catalog():
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported game-porting catalog version")
    return data


def validate_game_catalog():
    data = game_catalog()
    platforms, tracks = set(data["platforms"]), set(data["tracks"])
    if not platforms or not tracks:
        raise ValueError("Game-porting catalog must include platforms and tracks")
    for name, tool in data["tools"].items():
        if not tool["url"].startswith("https://github.com/"):
            raise ValueError("Untrusted tool URL: " + name)
        if not set(tool["platforms"]) <= platforms or not set(tool["tracks"]) <= tracks:
            raise ValueError("Invalid platform/track references: " + name)
    return {"platforms": len(platforms), "tracks": len(tracks),
            "tools": len(data["tools"])}


def _elf_arch(header):
    if len(header) < 20:
        return None
    endian = "little" if header[5] == 1 else "big" if header[5] == 2 else None
    if not endian:
        return None
    machine = int.from_bytes(header[18:20], endian)
    return {
        3: "x86", 8: "MIPS", 20: "PowerPC", 21: "PowerPC64",
        40: "ARM", 62: "x86-64", 183: "AArch64",
    }.get(machine, "ELF machine " + str(machine))


def inspect_binary(binary):
    """Inspect at most 4 KiB; report bounded sample hash, never a full-file hash."""
    path = Path(binary).expanduser().resolve()
    if not path.is_file():
        raise ValueError("Binary file not found: " + str(path))
    with path.open("rb") as stream:
        header = stream.read(HEADER_BYTES)
    if not header:
        raise ValueError("Empty binary file")
    info = {
        "name": path.name,
        "size_bytes": path.stat().st_size,
        "header_sample_sha256": hashlib.sha256(header).hexdigest(),
        "sample_bytes": len(header),
        "format": "unknown",
        "architecture": "unknown",
        "platform": None,
        "evidence": "No recognized signature (extensions are not proof).",
    }
    magic = header[:4]
    if magic in (bytes.fromhex("80371240"), bytes.fromhex("37804012"),
                 bytes.fromhex("40123780")):
        info.update(format="Nintendo 64 ROM", architecture="MIPS R4300i",
                    platform="n64", evidence="Verified Nintendo 64 ROM byte-order magic.")
    elif header.startswith(b"PS-X EXE"):
        info.update(format="PS-X EXE", architecture="MIPS R3000A",
                    platform="ps1", evidence="Verified PS-X EXE magic.")
    elif magic == b"XEX2":
        info.update(format="Xbox 360 XEX", architecture="PowerPC Xenon",
                    platform="xbox360", evidence="Verified XEX2 container magic.")
    elif len(header) >= 0x20 and header[0x18:0x1c] == bytes.fromhex("5d1c9ea3"):
        info.update(format="Wii disc image", architecture="PowerPC Broadway",
                    platform="wii", evidence="Verified Wii disc magic at offset 0x18.")
    elif len(header) >= 0x20 and header[0x1c:0x20] == bytes.fromhex("c2339f3d"):
        info.update(format="GameCube disc image", architecture="PowerPC Gekko",
                    platform="gamecube", evidence="Verified GameCube disc magic at offset 0x1c.")
    elif header.startswith(b"\x7fELF"):
        info.update(format="ELF", architecture=_elf_arch(header) or "unknown",
                    evidence="ELF architecture identified; CPU alone does not establish console.")
    elif header.startswith(b"MZ") and len(header) >= 0x40:
        pe_offset = int.from_bytes(header[0x3c:0x40], "little")
        if 0 < pe_offset <= len(header) - 6 and header[pe_offset:pe_offset+4] == b"PE\x00\x00":
            machine = int.from_bytes(header[pe_offset+4:pe_offset+6], "little")
            cpu = {0x14c: "x86", 0x8664: "x86-64", 0xaa64: "AArch64"}.get(machine, "PE machine " + hex(machine))
            info.update(format="Windows PE", architecture=cpu,
                        platform="windows-pc", evidence="Verified MZ/PE headers and COFF machine.")
    elif header.startswith(b"\x00PBP"):
        info.update(format="PSP PBP package", architecture="MIPS Allegrex (package; executable not inspected)",
                    platform="psp", evidence="Verified PSP PBP container magic.")
    elif magic == b"PFS0":
        info.update(format="Nintendo Switch NSP (PFS0)", architecture="AArch64 (package; code not inspected)",
                    platform="switch", evidence="Verified PFS0 partition magic; Switch 2 is not distinguished.")
    elif len(header) >= 0x104 and header[0x100:0x104] == b"HEAD":
        info.update(format="Nintendo Switch XCI", architecture="AArch64 (cartridge image; code not inspected)",
                    platform="switch", evidence="Verified XCI HEAD magic at 0x100; Switch 2 is not distinguished.")
    elif len(header) >= 0x14 and header[0x10:0x14] == b"NRO0":
        info.update(format="Nintendo Switch NRO", architecture="AArch64",
                    platform="switch", evidence="Verified NRO0 magic at 0x10 (homebrew executable).")
    elif magic == b"NSO0":
        info.update(format="Nintendo Switch NSO", architecture="AArch64",
                    platform="switch", evidence="Verified NSO0 executable magic.")
    elif len(header) >= 8 and header[:4] == b"dex\n" and header[7:8] == b"\x00":
        info.update(format="Android DEX " + header[4:7].decode("ascii", "replace"),
                    architecture="Dalvik/ART bytecode", platform="android",
                    evidence="Verified DEX magic and version.")
    elif magic == b"PK\x03\x04":
        if b"BundleConfig.pb" in header or b"base/manifest/AndroidManifest.xml" in header:
            info.update(format="Android App Bundle (AAB)",
                        architecture="Dalvik/ART bytecode (+ optional native libraries)", platform="android",
                        evidence="ZIP entries in the inspected prefix match an Android App Bundle.")
        elif b"AndroidManifest.xml" in header or b"classes.dex" in header:
            info.update(format="Android APK",
                        architecture="Dalvik/ART bytecode (+ optional native libraries)", platform="android",
                        evidence="ZIP entries in the inspected prefix match an Android APK.")
        else:
            info.update(format="ZIP archive",
                        evidence="ZIP container; Android markers were not found in the inspected 4 KiB prefix.")
    elif magic == bytes.fromhex("4f153d1d"):
        info.update(format="PS4 SELF", architecture="x86-64 (signed container; code not inspected)",
                    platform="ps4", evidence="Verified PS4 SELF magic 4F 15 3D 1D.")
    elif magic == bytes.fromhex("5414f5ee"):
        info.update(format="PS5 SELF", architecture="x86-64 (signed container; code not inspected)",
                    platform="ps5", evidence="Verified PS5 SELF magic 54 14 F5 EE.")
    elif header.startswith(b"SCE\x00"):
        info.update(format="Sony SELF", evidence="Sony SELF signature alone does not distinguish PS3 from PS4.")
    return info


def _infer_track(goal, platform):
    text = goal.casefold()
    if any(term in text for term in ("matching", "decompil", "decompile", "byte-for-byte", "source reconstruction")):
        return "matching-decomp"
    if any(term in text for term in ("frame pacing", "shader", "vulkan", "stutter", "graphics compatibility", "runtime", "compatibility")):
        return "compatibility-runtime"
    if any(term in text for term in ("static recomp", "recompil", "recompiler")):
        return "static-recomp"
    if "native pc port" in text or "native port" in text:
        if platform in ("ps4", "ps5", "switch", "switch2", "windows-pc"):
            return "compatibility-runtime"
        if platform in ("n64", "ps1", "ps2", "ps3", "xbox360"):
            return "static-recomp"
    return "triage"


def assess_game_port(project, *, binary=None, platform=None, track="auto", goal=""):
    """Produce a grounded plan, without running compilers, agents, or downloads."""
    data = game_catalog()
    project_path = Path(project).expanduser().resolve()
    if not project_path.is_dir():
        raise ValueError("Project directory not found: " + str(project_path))
    if platform is not None and platform not in data["platforms"]:
        raise ValueError("Unknown platform: " + str(platform))
    if track not in TRACKS:
        raise ValueError("Unknown track: " + str(track))
    observed = inspect_binary(binary) if binary else None
    detected = observed["platform"] if observed else None
    if (detected and platform and detected != platform
            and platform not in COMPATIBLE_DECLARATIONS.get(detected, ())):
        raise ValueError("Explicit platform conflicts with verified binary signature: "
                         + platform + " versus " + detected)
    selected = platform or detected
    selected_track = _infer_track(goal, selected) if track == "auto" else track
    platforms = data["platforms"]
    available = []
    if selected and selected_track != "triage":
        for name, tool in data["tools"].items():
            if selected in tool["platforms"] and selected_track in tool["tracks"]:
                available.append({"name": name, **tool})
    warnings = []
    if selected is None:
        warnings.append("Platform unverified. Supply a recognized binary or --platform; no specialized tool is selected.")
    if observed and observed["platform"] is None:
        warnings.append("Observed CPU/format is not proof of console platform.")
    if selected_track == "triage":
        warnings.append("Track unverified. Use --track or state a precise project goal.")
    elif not available:
        warnings.append("No curated direct tool matches this platform/track; manual research is needed.")
    if selected == "ps4" and selected_track == "compatibility-runtime":
        warnings.append("shadPS4 is a compatibility research reference, not a push-button port generator.")
    if selected == "android":
        warnings.append("Android packages are routed to reverse-engineering: see wb-android-reverse-engineering "
                        "and utilities (jadx, Apktool, Frida).")
    if selected in ("ps5", "switch", "switch2"):
        warnings.append("Platform is user-declared only; curated runtimes are experimental and title-specific.")
    if selected in ("ps3", "ps4") and observed and observed["format"] == "Sony SELF":
        warnings.append("SELF generation is user-declared, not inferred from the header.")
    if selected_track == "matching-decomp":
        warnings.append("decompdecomp's current built-in agents replace the obsolete decomp.wtf MCP workflow.")
    skills_by_track = {
        "matching-decomp": ["wb-decompilation-research", "wb-reverse-engineering"],
        "static-recomp": ["wb-binary-recompilation", "wb-reverse-engineering"],
        "compatibility-runtime": ["wb-vulkan-frame-pacing", "wb-shader-cache-triage",
                                  "wb-gameplay-acceptance"],
        "triage": ["wb-binary-analysis", "wb-reverse-engineering"],
    }
    active_skills = skills_by_track[selected_track]
    active = data["tracks"][selected_track]
    return {
        "project": str(project_path),
        "goal": goal,
        "binary": observed,
        "platform": selected,
        "platform_provenance": ("user-declared" if platform else "verified-signature" if detected else "unknown"),
        "platform_details": platforms.get(selected),
        "track": selected_track,
        "track_source": "explicit" if track != "auto" else "goal-signal" if selected_track != "triage" else "unresolved",
        "workflow": {"name": active["label"], "description": active["description"],
                     "validation": active["validation"]},
        "tools": available,
        "recommended_areas": sorted(GAME_AREAS.intersection({
            "matching-decomp": {"decompilation", "reverse-engineering"},
            "static-recomp": {"recompilation", "reverse-engineering", "game-port"},
            "compatibility-runtime": {"game-port", "reverse-engineering"},
            "triage": {"reverse-engineering"},
        }[selected_track])),
        "recommended_skills": active_skills,
        "suggested_mcps": ["github", "context7"],
        "mcp_policy": "suggest only; no server installed or activated",
        "agent_context": {
            "source": "read-only game-port assessment",
            "instructions": [
                "Read AGENTS.md and AI-WORKBENCH.md when present.",
                "Treat platform declarations as claims until binary provenance is established.",
                "Select only relevant project skills. Never assume an MCP or compiler is installed.",
                "Record build ID, original hash, offsets, toolchain and reproducible tests.",
                "Plan the smallest verified step before changing code.",
            ],
        },
        "warnings": warnings,
        "read_only": True,
    }


def game_port_markdown(plan):
    platform = plan["platform_details"]
    lines = [
        "# Game Reverse Engineering & Porting — Assessment", "",
        "Platform: " + (platform["label"] if platform else "unknown")
            + " (" + plan["platform_provenance"] + ")",
        "Track: " + plan["workflow"]["name"] + " (" + plan["track_source"] + ")",
        "CPU: " + (plan["binary"]["architecture"] if plan["binary"] else platform["cpu"] if platform else "unknown"),
        "Goal: " + (plan["goal"] or "not specified"), "",
        "## Evidence", "",
    ]
    if plan["binary"]:
        b = plan["binary"]
        lines.extend(["- File: " + b["name"], "- Format: " + b["format"],
                      "- Size: " + str(b["size_bytes"]) + " bytes",
                      "- First " + str(b["sample_bytes"]) + " bytes SHA-256: " + b["header_sample_sha256"],
                      "- Signature: " + b["evidence"]])
    else:
        lines.append("- No executable bytes inspected; platform assertions are unverified.")
    lines += ["", "## Recommended tools (not installed)", ""]
    lines += [
        "- " + tool["name"] + " — " + tool["url"] + " (" + tool["maturity"] + "): " + tool["note"]
        for tool in plan["tools"]
    ] or ["- None selected without sufficient platform and workflow evidence."]
    lines += ["", "## Workbench skills (not installed)", ""]
    lines.extend("- " + skill for skill in plan["recommended_skills"])
    lines += ["", "## Validation checklist", ""]
    lines.extend("- " + item for item in plan["workflow"]["validation"])
    lines += ["", "## Agent handoff", ""]
    lines.extend("- " + item for item in plan["agent_context"]["instructions"])
    if plan["warnings"]:
        lines += ["", "## Limitations and open questions", ""]
        lines.extend("- " + w for w in plan["warnings"])
    lines += ["", "This is a read-only recommendation. No executables were run or changed.", ""]
    return "\n".join(lines)


def save_game_plan(project, plan):
    """Opt-in private handoff; never writes to or copies the game binary."""
    root = Path(project).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Project directory not found: " + str(root))
    private = root / ".ai-workbench"
    private.mkdir(exist_ok=True)
    target = private / "GAME_PORT_PLAN.md"
    if target.is_symlink():
        raise ValueError("Refusing to overwrite a symlinked game-port plan")
    target.write_text(game_port_markdown(plan), encoding="utf-8")
    return target

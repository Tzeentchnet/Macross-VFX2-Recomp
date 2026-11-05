#!/usr/bin/env python3
"""Generate a local PSXRecomp package from NXP1000's English xdelta patch."""

from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import os
import platform
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import uuid
import zipfile
from pathlib import Path
from typing import Iterable


PACKAGE_ID = "macross.localization.english"
PACKAGE_VERSION = "1.0.0"
GENERATOR_VERSION = 2

SECTOR_SIZE = 2352
USER_DATA_OFFSET = 24
USER_DATA_SIZE = 2048

SOURCE_SIZE = 430_867_584
SOURCE_SHA256 = "ba4cd0051cb51705c14401136a29f3364cccab83afb60d24929551a835dd56c1"
PATCHED_SHA256 = "d280676a7a36c6cbb3ece7cc5a589433d64f8c1687f557fd54ee7691e1a2f801"

PATCH_NAME = "Macross_VFX2_ENG.xdelta"
PATCH_URL = (
    "https://github.com/NXP1000/Macross-VFX2-English/releases/download/"
    f"v1.0/{PATCH_NAME}"
)
PATCH_SIZE = 191_636
PATCH_SHA256 = "e26291021c82e49a4c7e429c82fa729775ba6311df757e6355a28335c7caa66a"

XDELTA_VERSION = "3.2.2"
XDELTA_RELEASE = (
    f"https://github.com/jmacd/xdelta/releases/download/v{XDELTA_VERSION}"
)
XDELTA_ASSETS = {
    ("windows", "x86_64"): (
        f"xdelta3-{XDELTA_VERSION}-windows-x86_64.zip",
        "d48f7651d86b78fdca397057b46601f89131f37219675df736db70af44ec3379",
    ),
    ("windows", "arm64"): (
        f"xdelta3-{XDELTA_VERSION}-windows-arm64.zip",
        "877bd98df8aa6665038029e5839fe4d768f029f5eff0f4a1671dac409fc0ce7d",
    ),
    ("linux", "x86_64"): (
        f"xdelta3-{XDELTA_VERSION}-linux-x86_64.tar.gz",
        "a8ce7d2c943ae2b3d308942643cb36d4805a1f16775abe1be64fee292d7c2506",
    ),
    ("linux", "arm64"): (
        f"xdelta3-{XDELTA_VERSION}-linux-arm64.tar.gz",
        "5efd11af8eb3b74bad056908281b6ffb8a2c0c165955fa643a5a267dfdeb9120",
    ),
    ("macos", "x86_64"): (
        f"xdelta3-{XDELTA_VERSION}-macos-x86_64.tar.gz",
        "e217f4d0f92357ee890f9d8b5571f7eb836a86ff87e8834bed0b9d9b38630f86",
    ),
    ("macos", "arm64"): (
        f"xdelta3-{XDELTA_VERSION}-macos-arm64.tar.gz",
        "27dcf763beb075ed28061ef136613f4bc6ea3999cb424f23a7d59f18ca2d7c8b",
    ),
}

EXPECTED_CHANGED_SECTORS = 310
EXPECTED_CHANGED_USER_BYTES = 221_336
EXPECTED_CHANGED_FILES = {
    "DATA00/BRF/IMGMSN01.TIX",
    "DATA00/BRF/IMGMSN02.TIX",
    "DATA00/BRF/IMGMSN03.TIX",
    "DATA00/BRF/IMGMSN04.TIX",
    "DATA00/BRF/IMGMSN05.TIX",
    "DATA00/BRF/IMGMSN07.TIX",
    "DATA00/BRF/IMGMSN08.TIX",
    "DATA00/BRF/IMGMSN09.TIX",
    "DATA00/BRF/IMGMSN10.TIX",
    "DATA00/BRF/IMGMSN11.TIX",
    "DATA00/BRF/IMGMSN12.TIX",
    "DATA00/BRF/IMGMSN14.TIX",
    "DATA00/IMAGE020.TIX",
    "DATA00/IMAGE040.TIX",
    "SYSTEM/ADJUST.TIX",
}


class PreparationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def default_cache_dir() -> Path:
    override = os.environ.get("MACROSSVFX2_CACHE_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        return base / "MacrossVFX2Recomp" / "cache"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "MacrossVFX2Recomp"
    base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "macross-vfx2-recomp"


def download_verified(
    url: str,
    destination: Path,
    expected_sha256: str,
    expected_size: int | None = None,
) -> Path:
    if destination.is_file():
        if (
            (expected_size is None or destination.stat().st_size == expected_size)
            and sha256_file(destination) == expected_sha256
        ):
            return destination
        destination.unlink()

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(
        f".{destination.name}.{os.getpid()}.{uuid.uuid4().hex}.part"
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Macross-VFX2-Recomp-English-Localization/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            with temporary.open("wb") as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
        if expected_size is not None and temporary.stat().st_size != expected_size:
            raise PreparationError(
                f"downloaded {destination.name} has size {temporary.stat().st_size}, "
                f"expected {expected_size}"
            )
        actual = sha256_file(temporary)
        if actual != expected_sha256:
            raise PreparationError(
                f"downloaded {destination.name} has SHA-256 {actual}, "
                f"expected {expected_sha256}"
            )
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def host_platform() -> tuple[str, str]:
    if sys.platform == "win32":
        system = "windows"
    elif sys.platform == "darwin":
        system = "macos"
    elif sys.platform.startswith("linux"):
        system = "linux"
    else:
        raise PreparationError(f"unsupported host platform: {sys.platform}")

    machine = platform.machine().lower()
    if machine in {"amd64", "x86_64"}:
        architecture = "x86_64"
    elif machine in {"arm64", "aarch64"}:
        architecture = "arm64"
    else:
        raise PreparationError(f"unsupported host architecture: {machine}")
    return system, architecture


def safe_archive_target(root: Path, member: str) -> Path:
    target = (root / member).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise PreparationError(f"archive entry escapes its destination: {member}") from exc
    return target


def extract_archive(archive: Path, destination: Path) -> None:
    temporary = destination.with_name(
        f".{destination.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    )
    shutil.rmtree(temporary, ignore_errors=True)
    temporary.mkdir(parents=True)
    try:
        if archive.suffix.lower() == ".zip":
            with zipfile.ZipFile(archive) as source:
                for member in source.infolist():
                    safe_archive_target(temporary, member.filename)
                source.extractall(temporary)
        else:
            with tarfile.open(archive, "r:*") as source:
                for member in source.getmembers():
                    safe_archive_target(temporary, member.name)
                    if member.issym() or member.islnk():
                        raise PreparationError(
                            f"xdelta archive contains an unsupported link: {member.name}"
                        )
                source.extractall(temporary)

        backup = destination.with_name(
            f".{destination.name}.{os.getpid()}.{uuid.uuid4().hex}.old"
        )
        if destination.exists():
            destination.rename(backup)
        try:
            temporary.rename(destination)
        except Exception:
            if backup.exists():
                backup.rename(destination)
            raise
        shutil.rmtree(backup, ignore_errors=True)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def ensure_xdelta(cache_dir: Path, override: Path | None) -> Path:
    if override is not None:
        executable = override.expanduser().resolve()
        if not executable.is_file():
            raise PreparationError(f"xdelta3 executable does not exist: {executable}")
        return executable

    system, architecture = host_platform()
    try:
        asset_name, asset_sha256 = XDELTA_ASSETS[(system, architecture)]
    except KeyError as exc:
        raise PreparationError(
            f"no pinned xdelta3 build for {system}/{architecture}"
        ) from exc

    tool_root = cache_dir / "tools" / f"xdelta3-{XDELTA_VERSION}-{system}-{architecture}"
    executable_name = "xdelta3.exe" if system == "windows" else "xdelta3"
    matches = list(tool_root.rglob(executable_name)) if tool_root.exists() else []
    if len(matches) == 1 and matches[0].is_file():
        return matches[0]

    archive = download_verified(
        f"{XDELTA_RELEASE}/{asset_name}",
        cache_dir / "downloads" / asset_name,
        asset_sha256,
    )
    extract_archive(archive, tool_root)
    matches = list(tool_root.rglob(executable_name))
    if len(matches) != 1:
        raise PreparationError(
            f"expected one {executable_name} in {asset_name}, found {len(matches)}"
        )
    executable = matches[0]
    if system != "windows":
        executable.chmod(executable.stat().st_mode | 0o111)
    return executable


def ensure_patch(cache_dir: Path, override: Path | None) -> Path:
    if override is not None:
        patch = override.expanduser().resolve()
        if not patch.is_file():
            raise PreparationError(f"English patch does not exist: {patch}")
        if patch.stat().st_size != PATCH_SIZE or sha256_file(patch) != PATCH_SHA256:
            raise PreparationError(
                f"{patch} is not the supported NXP1000 v1.0 patch "
                f"(expected SHA-256 {PATCH_SHA256})"
            )
        return patch
    return download_verified(
        PATCH_URL,
        cache_dir / "downloads" / "macross-vfx2-english-v1.0" / PATCH_NAME,
        PATCH_SHA256,
        PATCH_SIZE,
    )


def apply_xdelta(xdelta: Path, source: Path, patch: Path, output: Path) -> None:
    command = [
        str(xdelta),
        "-f",
        "-d",
        "-s",
        str(source),
        str(patch),
        str(output),
    ]
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise PreparationError(
            f"xdelta3 failed with exit code {result.returncode}: {detail}"
        )


def group_contiguous(values: Iterable[int]) -> list[tuple[int, int]]:
    ordered = sorted(set(values))
    if not ordered:
        return []
    groups: list[tuple[int, int]] = []
    start = previous = ordered[0]
    for value in ordered[1:]:
        if value == previous + 1:
            previous = value
            continue
        groups.append((start, previous))
        start = previous = value
    groups.append((start, previous))
    return groups


def user_sector(image: mmap.mmap, lba: int) -> bytes:
    start = lba * SECTOR_SIZE + USER_DATA_OFFSET
    return image[start : start + USER_DATA_SIZE]


def user_range(image: mmap.mmap, lba: int, size: int) -> bytes:
    count = (size + USER_DATA_SIZE - 1) // USER_DATA_SIZE
    return b"".join(user_sector(image, lba + index) for index in range(count))[:size]


def iso_file_extents(image: mmap.mmap) -> dict[str, tuple[int, int]]:
    pvd = user_sector(image, 16)
    if pvd[0] != 1 or pvd[1:6] != b"CD001" or pvd[6] != 1:
        raise PreparationError("source Track 1 does not contain the expected ISO 9660 PVD")

    root_size = pvd[156]
    root = pvd[156 : 156 + root_size]
    root_lba = struct.unpack_from("<I", root, 2)[0]
    root_length = struct.unpack_from("<I", root, 10)[0]
    files: dict[str, tuple[int, int]] = {}
    visited: set[tuple[int, int]] = set()

    def walk(path: str, lba: int, size: int) -> None:
        key = (lba, size)
        if key in visited:
            return
        visited.add(key)
        directory = user_range(image, lba, size)
        offset = 0
        while offset < len(directory):
            record_size = directory[offset]
            if record_size == 0:
                offset = ((offset // USER_DATA_SIZE) + 1) * USER_DATA_SIZE
                continue
            record = directory[offset : offset + record_size]
            offset += record_size
            if len(record) < 34:
                raise PreparationError(f"invalid ISO directory record under {path or '/'}")
            extent = struct.unpack_from("<I", record, 2)[0]
            length = struct.unpack_from("<I", record, 10)[0]
            flags = record[25]
            name_size = record[32]
            raw_name = bytes(record[33 : 33 + name_size])
            if raw_name in {b"\x00", b"\x01"}:
                continue
            try:
                name = raw_name.decode("ascii")
            except UnicodeDecodeError:
                name = raw_name.decode("shift_jis")
            name = name.split(";", 1)[0]
            full_name = f"{path}/{name}" if path else name
            if flags & 2:
                walk(full_name, extent, length)
            else:
                files[full_name] = (extent, length)

    walk("", root_lba, root_length)
    return files


def changed_localization_sectors(
    stock: mmap.mmap, patched: mmap.mmap
) -> tuple[list[int], int, set[str]]:
    if len(stock) != len(patched) or len(stock) % SECTOR_SIZE != 0:
        raise PreparationError("patched Track 1 geometry does not match the stock image")

    changed_lbas: list[int] = []
    changed_user_bytes = 0
    for lba in range(len(stock) // SECTOR_SIZE):
        start = lba * SECTOR_SIZE
        stock_sector = stock[start : start + SECTOR_SIZE]
        patched_sector = patched[start : start + SECTOR_SIZE]
        if stock_sector == patched_sector:
            continue
        if stock_sector[:USER_DATA_OFFSET] != patched_sector[:USER_DATA_OFFSET]:
            raise PreparationError(f"English patch changes raw sector headers at LBA {lba}")
        if stock_sector[15] != 2 or stock_sector[18] & 0x20:
            raise PreparationError(
                f"English patch changes a non-Mode-2-Form-1 sector at LBA {lba}"
            )
        stock_user = stock_sector[
            USER_DATA_OFFSET : USER_DATA_OFFSET + USER_DATA_SIZE
        ]
        patched_user = patched_sector[
            USER_DATA_OFFSET : USER_DATA_OFFSET + USER_DATA_SIZE
        ]
        if stock_user == patched_user:
            raise PreparationError(
                f"English patch changes only raw parity data at LBA {lba}"
            )
        changed_lbas.append(lba)
        changed_user_bytes += sum(
            before != after for before, after in zip(stock_user, patched_user)
        )

    files = iso_file_extents(stock)
    changed_files: set[str] = set()
    unmapped = set(changed_lbas)
    for name, (lba, size) in files.items():
        sector_count = (size + USER_DATA_SIZE - 1) // USER_DATA_SIZE
        overlaps = unmapped.intersection(range(lba, lba + sector_count))
        if overlaps:
            changed_files.add(name)
            unmapped.difference_update(overlaps)
    if unmapped:
        raise PreparationError(
            "English patch changes sectors outside ISO files: "
            + ", ".join(str(lba) for lba in sorted(unmapped))
        )
    return changed_lbas, changed_user_bytes, changed_files


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_manifest(overlays: list[dict[str, object]]) -> str:
    lines = [
        "format_version = 10",
        f"id = {toml_string(PACKAGE_ID)}",
        f"version = {toml_string(PACKAGE_VERSION)}",
        'name = "English Localization"',
        (
            'author = "NXP1000, PixelatedShinobi, daburuwosagase, '
            'and getterdrill"'
        ),
        (
            'description = "English mission briefings and Variable Fighter '
            'descriptions from the verified NXP1000 v1.0 patch."'
        ),
        'source_name = "NXP1000/Macross-VFX2-English v1.0"',
        'source_url = "https://github.com/NXP1000/Macross-VFX2-English"',
        'resolver = "declarative"',
        'save_compatibility = "shared"',
        "",
        "[[author_link]]",
        'name = "NXP1000"',
        'url = "https://github.com/NXP1000"',
        "",
        "[[target]]",
        'game_id = "SLPS-02237"',
        f'disc_sha256 = "{SOURCE_SHA256}"',
        "",
        "[[feature]]",
        'id = "english"',
        'name = "English Localization"',
        (
            'description = "Translates mission briefing graphics, Variable '
            'Fighter descriptions, and related interface text. Enabled by default."'
        ),
        'group = "Localization"',
        "default_enabled = true",
        "quick = true",
    ]
    for overlay in overlays:
        lines.extend(
            [
                "",
                "[[overlay]]",
                'feature = "english"',
                'target = "disc_user"',
                f"offset = {overlay['offset']}",
                f"file = {toml_string(str(overlay['file']))}",
                f'sha256 = "{overlay["sha256"]}"',
                f'expected_sha256 = "{overlay["expected_sha256"]}"',
            ]
        )
    return "\n".join(lines) + "\n"


def package_is_current(package_dir: Path) -> bool:
    receipt_path = package_dir / "generation.json"
    manifest_path = package_dir / "manifest.toml"
    if not receipt_path.is_file() or not manifest_path.is_file():
        return False
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    expected = {
        "schema": 1,
        "generator_version": GENERATOR_VERSION,
        "package_id": PACKAGE_ID,
        "package_version": PACKAGE_VERSION,
        "source_sha256": SOURCE_SHA256,
        "patch_sha256": PATCH_SHA256,
        "patched_sha256": PATCHED_SHA256,
        "changed_sectors": EXPECTED_CHANGED_SECTORS,
        "changed_user_bytes": EXPECTED_CHANGED_USER_BYTES,
    }
    if any(receipt.get(key) != value for key, value in expected.items()):
        return False
    overlays = receipt.get("overlays")
    if not isinstance(overlays, list) or not overlays:
        return False
    for overlay in overlays:
        relative = overlay.get("file")
        digest = overlay.get("sha256")
        if not isinstance(relative, str) or not isinstance(digest, str):
            return False
        asset = package_dir / relative
        if not asset.is_file() or sha256_file(asset) != digest:
            return False
    return sha256_file(manifest_path) == receipt.get("manifest_sha256")


def publish_package(
    packages_dir: Path,
    stock: mmap.mmap,
    patched: mmap.mmap,
    changed_lbas: list[int],
    changed_user_bytes: int,
    changed_files: set[str],
) -> Path:
    package_root = packages_dir / PACKAGE_ID
    package_dir = package_root / PACKAGE_VERSION
    package_root.mkdir(parents=True, exist_ok=True)
    temporary = package_root / f".{PACKAGE_VERSION}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    temporary.mkdir()
    try:
        assets_dir = temporary / "assets"
        assets_dir.mkdir()
        overlays: list[dict[str, object]] = []
        for first, last in group_contiguous(changed_lbas):
            relative = f"assets/lba-{first:06d}-{last:06d}.bin"
            stock_data = b"".join(
                user_sector(stock, lba) for lba in range(first, last + 1)
            )
            patched_data = b"".join(
                user_sector(patched, lba) for lba in range(first, last + 1)
            )
            asset = temporary / relative
            asset.write_bytes(patched_data)
            overlays.append(
                {
                    "offset": first * USER_DATA_SIZE,
                    "file": relative,
                    "size": len(patched_data),
                    "sha256": sha256_bytes(patched_data),
                    "expected_sha256": sha256_bytes(stock_data),
                }
            )

        manifest = build_manifest(overlays)
        manifest_path = temporary / "manifest.toml"
        manifest_path.write_text(manifest, encoding="utf-8", newline="\n")
        readme = (
            "English Localization for Macross VF-X2 Recompiled\n"
            "=================================================\n\n"
            "Generated locally from the verified stock Track 1 and NXP1000's\n"
            "Macross VF-X 2 English v1.0 xdelta release. The upstream patch is\n"
            "downloaded from its official GitHub release and is not stored in\n"
            "the project repository.\n\n"
            f"Upstream: https://github.com/NXP1000/Macross-VFX2-English\n"
            f"Patch SHA-256: {PATCH_SHA256}\n"
            f"Stock Track 1 SHA-256: {SOURCE_SHA256}\n"
            f"Patched Track 1 SHA-256: {PATCHED_SHA256}\n\n"
            "Translation credits: PixelatedShinobi, daburuwosagase, and\n"
            "getterdrill. Patch release and repository: NXP1000.\n\n"
            "This directory contains only locally generated, hash-guarded\n"
            "overlay payloads. Do not commit it or include it in a public\n"
            "release without permission from the upstream patch authors.\n"
        )
        (temporary / "README.txt").write_text(readme, encoding="utf-8", newline="\n")
        receipt = {
            "schema": 1,
            "generator_version": GENERATOR_VERSION,
            "package_id": PACKAGE_ID,
            "package_version": PACKAGE_VERSION,
            "source_sha256": SOURCE_SHA256,
            "patch_url": PATCH_URL,
            "patch_sha256": PATCH_SHA256,
            "patched_sha256": PATCHED_SHA256,
            "changed_sectors": len(changed_lbas),
            "changed_user_bytes": changed_user_bytes,
            "changed_files": sorted(changed_files),
            "manifest_sha256": sha256_file(manifest_path),
            "overlays": overlays,
        }
        (temporary / "generation.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        backup = package_root / f".{PACKAGE_VERSION}.{os.getpid()}.{uuid.uuid4().hex}.old"
        if package_dir.exists():
            package_dir.rename(backup)
        try:
            temporary.rename(package_dir)
        except Exception:
            if backup.exists():
                backup.rename(package_dir)
            raise
        shutil.rmtree(backup, ignore_errors=True)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return package_dir


def clean_package(packages_dir: Path) -> None:
    package_root = packages_dir / PACKAGE_ID
    if package_root.exists():
        shutil.rmtree(package_root)


def prepare(args: argparse.Namespace) -> Path:
    source = args.source_track.expanduser().resolve()
    packages_dir = args.packages_dir.expanduser().resolve()
    cache_dir = args.cache_dir.expanduser().resolve()
    if not source.is_file():
        raise PreparationError(f"stock Track 1 does not exist: {source}")
    if source.stat().st_size != SOURCE_SIZE:
        raise PreparationError(
            f"stock Track 1 has size {source.stat().st_size}, expected {SOURCE_SIZE}"
        )
    actual_source_sha256 = sha256_file(source)
    if actual_source_sha256 != SOURCE_SHA256:
        raise PreparationError(
            f"stock Track 1 has SHA-256 {actual_source_sha256}, "
            f"expected {SOURCE_SHA256}"
        )

    package_dir = packages_dir / PACKAGE_ID / PACKAGE_VERSION
    if package_is_current(package_dir):
        return package_dir

    patch = ensure_patch(cache_dir, args.patch)
    xdelta = ensure_xdelta(cache_dir, args.xdelta3)
    with tempfile.TemporaryDirectory(prefix="macross-vfx2-english-") as temp:
        patched_path = Path(temp) / "Track1-English.bin"
        apply_xdelta(xdelta, source, patch, patched_path)
        if patched_path.stat().st_size != SOURCE_SIZE:
            raise PreparationError(
                f"patched Track 1 has size {patched_path.stat().st_size}, "
                f"expected {SOURCE_SIZE}"
            )
        actual_patched_sha256 = sha256_file(patched_path)
        if actual_patched_sha256 != PATCHED_SHA256:
            raise PreparationError(
                f"patched Track 1 has SHA-256 {actual_patched_sha256}, "
                f"expected {PATCHED_SHA256}"
            )

        with source.open("rb") as stock_stream, patched_path.open("rb") as patched_stream:
            with mmap.mmap(stock_stream.fileno(), 0, access=mmap.ACCESS_READ) as stock:
                with mmap.mmap(
                    patched_stream.fileno(), 0, access=mmap.ACCESS_READ
                ) as patched:
                    changed_lbas, changed_user_bytes, changed_files = (
                        changed_localization_sectors(stock, patched)
                    )
                    if len(changed_lbas) != EXPECTED_CHANGED_SECTORS:
                        raise PreparationError(
                            f"English patch changes {len(changed_lbas)} sectors, "
                            f"expected {EXPECTED_CHANGED_SECTORS}"
                        )
                    if changed_user_bytes != EXPECTED_CHANGED_USER_BYTES:
                        raise PreparationError(
                            f"English patch changes {changed_user_bytes} user bytes, "
                            f"expected {EXPECTED_CHANGED_USER_BYTES}"
                        )
                    if changed_files != EXPECTED_CHANGED_FILES:
                        missing = sorted(EXPECTED_CHANGED_FILES - changed_files)
                        extra = sorted(changed_files - EXPECTED_CHANGED_FILES)
                        raise PreparationError(
                            "English patch file scope changed; "
                            f"missing={missing}, extra={extra}"
                        )
                    return publish_package(
                        packages_dir,
                        stock,
                        patched,
                        changed_lbas,
                        changed_user_bytes,
                        changed_files,
                    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-track", type=Path)
    parser.add_argument("--packages-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, default=default_cache_dir())
    parser.add_argument(
        "--patch",
        type=Path,
        help="optional local copy of the exact NXP1000 v1.0 xdelta",
    )
    parser.add_argument(
        "--xdelta3",
        type=Path,
        help="optional local xdelta3 executable with LZMA support",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="remove only the generated localization package",
    )
    args = parser.parse_args()
    if not args.clean and args.source_track is None:
        parser.error("--source-track is required unless --clean is used")
    return args


def main() -> int:
    args = parse_args()
    try:
        if args.clean:
            clean_package(args.packages_dir.expanduser().resolve())
            print("English localization package is not staged")
            return 0
        package = prepare(args)
        print(f"English localization package ready: {package}")
        return 0
    except (OSError, PreparationError, subprocess.SubprocessError) as exc:
        print(f"English localization preparation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

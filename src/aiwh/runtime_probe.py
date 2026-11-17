"""Local hardware and AI runtime probe (read-only, zero paid providers)."""
from __future__ import annotations

import ctypes
import json
import os
import platform
import shutil
import subprocess
import urllib.error
import urllib.request


def _total_ram_gb():
    if os.name == 'nt':
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ('dwLength', ctypes.c_ulong),
                ('dwMemoryLoad', ctypes.c_ulong),
                ('ullTotalPhys', ctypes.c_ulonglong),
                ('ullAvailPhys', ctypes.c_ulonglong),
                ('ullTotalPageFile', ctypes.c_ulonglong),
                ('ullAvailPageFile', ctypes.c_ulonglong),
                ('ullTotalVirtual', ctypes.c_ulonglong),
                ('ullAvailVirtual', ctypes.c_ulonglong),
                ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return round(stat.ullTotalPhys / (1024 ** 3), 1)
    elif hasattr(os, 'sysconf') and 'SC_PHYS_PAGES' in os.sysconf_names:
        pages = os.sysconf('SC_PHYS_PAGES')
        page_size = os.sysconf('SC_PAGE_SIZE')
        if pages > 0 and page_size > 0:
            return round((pages * page_size) / (1024 ** 3), 1)
    return None


def _nvidia_gpus():
    exe = shutil.which('nvidia-smi')
    if not exe:
        return []
    try:
        proc = subprocess.run(
            [exe, '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, encoding='utf-8', timeout=3, check=False,
        )
        if proc.returncode != 0:
            return []
        gpus = []
        for line in proc.stdout.splitlines():
            parts = [p.strip() for p in line.split(',')]
            if len(parts) == 2 and parts[1].isdigit():
                gpus.append({'name': parts[0], 'vram_gb': round(int(parts[1]) / 1024, 1)})
        return gpus
    except (OSError, subprocess.TimeoutExpired):
        return []


def _ollama_models(url='http://127.0.0.1:11434/api/tags'):
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return [m.get('name') for m in data.get('models', []) if isinstance(m, dict) and m.get('name')]
    except (OSError, ValueError, urllib.error.URLError):
        return None


def probe_hardware():
    """Inspect local CPU, RAM, GPU and optional Ollama runtime without modifying anything."""
    ram_gb = _total_ram_gb()
    gpus = _nvidia_gpus()
    max_vram = max((g['vram_gb'] for g in gpus), default=0.0)
    ollama = _ollama_models()
    if max_vram >= 16:
        tier = 'gpu-16gb+ (14B-32B quantized local LLMs + ONNX embeddings)'
    elif max_vram >= 8:
        tier = 'gpu-8gb (7B-14B quantized local LLMs + ONNX embeddings)'
    elif (ram_gb or 0) >= 16:
        tier = 'cpu-16gb+ (ONNX embeddings via fastembed + small 3B-7B CPU models)'
    else:
        tier = 'lightweight-cpu (SQLite FTS5 lexical + lightweight ONNX embeddings)'
    return {
        'os': platform.system(),
        'arch': platform.machine(),
        'cpu_count': os.cpu_count(),
        'ram_gb': ram_gb,
        'gpus': gpus,
        'ollama_running': ollama is not None,
        'ollama_models': ollama or [],
        'recommended_local_tier': tier,
    }

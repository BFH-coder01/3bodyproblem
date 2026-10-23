"""Read-only local prerequisites and GPU/toolchain inventory; no execution benchmark."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

OUTPUT_LIMIT = 24_000
DEFAULT_TIMEOUT = 10


def _text(value):
    if value is None:
        return ''
    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value


def probe(command, *, timeout=DEFAULT_TIMEOUT, which=shutil.which, runner=subprocess.run):
    """Run a fixed read-only argv, with bounded elapsed time and reported output."""
    executable = which(command[0])
    result = {'command': command, 'timeout_s': timeout, 'status': 'missing',
              'returncode': None, 'stdout': '', 'stderr': '', 'truncated': False}
    if executable is None:
        return result
    try:
        completed = runner([executable, *command[1:]], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=timeout, check=False)
        result.update(status='ok' if completed.returncode == 0 else 'error',
                      returncode=completed.returncode,
                      stdout=_text(completed.stdout), stderr=_text(completed.stderr))
    except subprocess.TimeoutExpired as error:
        result.update(status='timeout', stdout=_text(error.stdout), stderr=_text(error.stderr))
    except OSError as error:
        result.update(status='error', stderr=f'{type(error).__name__}: {error.strerror or "Unable to run utility"}')
    for stream in ('stdout', 'stderr'):
        if len(result[stream]) > OUTPUT_LIMIT:
            result[stream] = result[stream][:OUTPUT_LIMIT]
            result['truncated'] = True
    return result


def physical_memory():
    """Return OS-reported host RAM, independently of GPU memory."""
    try:
        if os.name != 'nt':
            return int(os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE'))
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong),
                        *[(name, ctypes.c_ulonglong) for name in (
                            'total_physical', 'available_physical', 'total_page_file',
                            'available_page_file', 'total_virtual', 'available_virtual',
                            'available_extended_virtual')]]

        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        return int(status.total_physical) if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)) else None
    except (AttributeError, OSError, ValueError):
        return None


def collect(*, system=None, run_probe=probe):
    system = system or platform.system()
    tools = {
        'git': run_probe(['git', '--version']),
        'node': run_probe(['node', '--version']),
        'hipcc': run_probe(['hipcc', '--version']),
    }
    gpu = {'source': None, 'devices': [], 'notes': []}
    if system == 'Windows':
        # Win32_VideoController.AdapterRAM can truncate above 4 GiB. Do not use it.
        script = ('Get-CimInstance Win32_VideoController -ErrorAction Stop | '
                  'Select-Object Name,PNPDeviceID,DriverVersion | ConvertTo-Json -Depth 3 -Compress')
        tools['video_controllers'] = run_probe([
            'powershell', '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', script])
        video = tools['video_controllers']
        gpu['source'] = 'Win32_VideoController'
        if video['status'] == 'ok':
            try:
                devices = json.loads(video['stdout'])
                if isinstance(devices, dict):
                    devices = [devices]
                if not isinstance(devices, list):
                    raise ValueError('Expected controller list')
                gpu['devices'] = [{key: item.get(key) for key in ('Name', 'PNPDeviceID', 'DriverVersion')}
                                  for item in devices if isinstance(item, dict)]
            except (ValueError, TypeError):
                gpu['notes'].append('Controller utility returned invalid or truncated JSON; inspect tool status/output.')
        gpu['notes'].append('GPU VRAM is not inferred from Win32_VideoController.AdapterRAM.')
        tools['rocminfo'] = {'status': 'not_applicable', 'reason': 'Linux runtime probe not attempted on Windows'}
    elif system == 'Linux':
        tools['lspci'] = run_probe(['lspci', '-nn'])
        # Keep display-controller evidence, not unrelated PCI hardware details.
        pci = tools['lspci']
        lines = [line for line in pci.get('stdout', '').splitlines()
                 if re.search(r'VGA compatible controller|3D controller|Display controller', line, re.I)]
        pci['stdout'] = '\n'.join(lines)
        pci['filtered_to_display_controllers'] = True
        gpu.update(source='lspci', devices=[{'description': line} for line in lines])
        tools['rocminfo'] = run_probe(['rocminfo'])
        tools['rocm_smi'] = run_probe(['rocm-smi', '--showproductname', '--showdriverversion', '--showmeminfo', 'vram', '--json'])
        tools['amd_smi'] = run_probe(['amd-smi', 'version'])
        gpu['notes'].append('rocminfo/SMI outputs are detection evidence; no GPU kernel was launched by this script.')
    else:
        gpu['notes'].append(f'GPU detection is not implemented for {system}.')
        tools['gpu_detection'] = {'status': 'not_applicable', 'reason': 'Unsupported operating system'}

    node = tools['node']
    node_version = re.match(r'^v?(\d+)\.', node.get('stdout', '').strip()) if node['status'] == 'ok' else None
    cpu = {'python_3_11_or_newer': sys.version_info >= (3, 11),
           'node_18_or_newer': bool(node_version and int(node_version.group(1)) >= 18),
           'git_available': tools['git']['status'] == 'ok'}
    cpu['ready'] = all(cpu.values())
    return {
        'schema_version': 'threebody.rig-inventory.v1',
        'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'platform': {'system': system, 'release': platform.release(), 'version': platform.version(),
                     'machine': platform.machine(), 'processor': platform.processor(),
                     'logical_cpus': os.cpu_count(), 'physical_ram_bytes': physical_memory()},
        'python': {'version': platform.python_version(), 'implementation': platform.python_implementation()},
        'tools': tools,
        'gpu': gpu,
        'assessment': {'cpu_pipeline': cpu,
                       'gpu_execution': {'status': 'not_tested',
                                         'reason': 'Inventory is not a HIP compile, numerical parity test, or GPU-backed run.'}},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, help='Write JSON evidence here instead of stdout; parent directory must exist')
    args = parser.parse_args(argv)
    report = json.dumps(collect(), indent=2, allow_nan=False) + '\n'
    if args.out:
        args.out.write_text(report, encoding='utf-8')
    else:
        print(report, end='')


if __name__ == '__main__':
    main()

# Rig inventory and acceptance

The CPU reference pipeline needs Python 3.11+, Node.js 18+ and Git. A successful host test does not establish RX 7900 XTX compatibility or execute a GPU kernel.

On the actual rig, from the repository root:

```powershell
New-Item -ItemType Directory -Force ..\artifacts | Out-Null
python scripts/rig_inventory.py --out ..\artifacts\rig-inventory.json
```

Linux equivalent:

```bash
mkdir -p ../artifacts
python3 scripts/rig_inventory.py --out ../artifacts/rig-inventory.json
```

Omit `--out` to print JSON. The file records the local OS, architecture, CPU count, OS-reported RAM, Python/Git/Node versions, HIP compiler probe and available GPU/runtime evidence. Each utility runs with a timeout, uses a fixed argument array and reports missing tools, errors or truncation. The script does not dump environment variables, contact the network, install drivers, change device state or launch a GPU workload. Only the requested output file is written. Keep rig evidence outside source control.

Windows uses a read-only `Get-CimInstance Win32_VideoController` query restricted to Name, PNPDeviceID and DriverVersion. It does not treat AdapterRAM as usable VRAM: that field can truncate above 4 GiB. Linux reports display controllers from lspci and probes rocminfo, HIP and available SMI utilities. Missing/incompatible utilities are evidence gaps, not automatic proof that a GPU is absent or unsupported. Truncated output may need a focused follow-up check.

The inventory supports the TBL-001 environment decision. It does not complete TBL-070. That gate still needs an approved OS/driver/runtime/compiler tuple, an actual HIP-backed smoke run on the RX 7900 XTX, recorded architecture and versions, execution logs, CPU/GPU numerical comparison and memory measurements. Do not mark compile-only work or CPU fallback as GPU success. No driver change or large campaign is authorized by running this script.

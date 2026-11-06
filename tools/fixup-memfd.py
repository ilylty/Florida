#!/usr/bin/env python3
"""
Fallback renamer for the memfd name, used when 0009-Florida-memfd-name-jit-cache
does not apply because the syscall enum spelling differs between frida releases:

  * <= 17.6.x : Linux.syscall (SysCall.memfd_create, name, flags)
  * >= 17.7.x : Linux.syscall (LinuxSyscall.MEMFD_CREATE, name, flags)

Keeps the memfd name out of /proc/self/maps as "memfd:frida-agent".
"""
import pathlib
import sys

TARGETS = [
    'Linux.syscall (SysCall.memfd_create, name, flags)',
    'Linux.syscall (LinuxSyscall.MEMFD_CREATE, name, flags)',
]

def main(argv):
    if len(argv) < 2:
        print("usage: fixup-memfd.py <frida-core root>")
        return 2

    path = pathlib.Path(argv[1]) / "lib" / "base" / "linux.vala"
    if not path.exists():
        print(f"!! {path} not found")
        return 1

    src = path.read_text()
    changed = False
    for t in TARGETS:
        if t in src:
            src = src.replace(t, t.replace(", name, flags)", ', "jit-cache", flags)'))
            changed = True
            print(f"[+] memfd name patched via: {t}")

    if not changed:
        # last resort: rewrite whatever call passes `name` right after memfd_create
        lines = src.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if "Linux.syscall" in line and "memfd" in line.lower() and "name, flags" in line:
                lines[i] = line.replace("name, flags", '"jit-cache", flags')
                changed = True
                print(f"[+] memfd name patched (line {i + 1}): {lines[i].strip()}")
        src = "".join(lines)

    if not changed:
        print("!! could not locate memfd_create syscall wrapper")
        return 1

    path.write_text(src)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))

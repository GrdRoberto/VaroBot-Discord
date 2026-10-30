import os
import glob
import time
import asyncio
import subprocess
from mcstatus import JavaServer
import config

prev_cpu_time = 0.0
prev_calc_time = 0.0

def _run_shell(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout.strip()
    except Exception:
        return ""

async def run_cmd(cmd: list[str]) -> str:
    return await asyncio.to_thread(_run_shell, cmd)

def get_power_usage() -> str:
    try:
        bat_dirs = glob.glob("/sys/class/power_supply/BAT*")
        if not bat_dirs:
            return "N/A (AC Power)"
        bat = bat_dirs[0]
        try:
            with open(f"{bat}/power_now", "r") as f:
                p = int(f.read().strip()) / 1e6
            return f"{p:.2f} W"
        except FileNotFoundError:
            with open(f"{bat}/voltage_now", "r") as f:
                v = int(f.read().strip()) / 1e6
            with open(f"{bat}/current_now", "r") as f:
                c = int(f.read().strip()) / 1e6
            return f"{v * c:.2f} W"
    except Exception:
        return "N/A (AC Power)"

def get_minecraft_folder_size(folder_path: str) -> str:
    try:
        if not os.path.isdir(folder_path):
            return "N/A"
        result = subprocess.run(["du", "-sh", folder_path], capture_output=True, text=True, check=False)
        return result.stdout.split()[0] if result.stdout else "N/A"
    except Exception:
        return "N/A"

def get_minecraft_resources() -> tuple[str, str]:
    global prev_cpu_time, prev_calc_time
    target_pid = None
    try:
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            exe_link = f"/proc/{entry}/exe"
            cmdline_path = f"/proc/{entry}/cmdline"
            try:
                cmd_raw = open(cmdline_path, "rb").read()
                cmd_args = [arg.decode("utf-8", errors="ignore") for arg in cmd_raw.split(b"\x00")]
                is_java = any("java" in arg.lower() for arg in cmd_args[:2]) or (
                    os.path.exists(exe_link) and "java" in os.path.basename(os.readlink(exe_link)).lower()
                )
                if is_java and any("server.jar" in arg for arg in cmd_args):
                    target_pid = entry
                    break
            except (PermissionError, ProcessLookupError, FileNotFoundError):
                continue

        if not target_pid:
            return f"0 MB / {config.MAX_ALLOCATED_RAM_MB} MB (0%)", "0.0%"

        rss_kb = 0
        with open(f"/proc/{target_pid}/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    rss_kb = int(line.split()[1])
                    break

        used_mb = int(rss_kb / 1024)
        pct = (used_mb / config.MAX_ALLOCATED_RAM_MB) * 100
        cpu_pct_str = "0.0%"
        clk_tck = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
        with open(f"/proc/{target_pid}/stat", "r") as f:
            stat_fields = f.read().split()

        utime = int(stat_fields[13])
        stime = int(stat_fields[14])
        total_time_sec = (utime + stime) / clk_tck
        now = time.time()

        if prev_calc_time > 0 and now > prev_calc_time:
            time_delta = now - prev_calc_time
            cpu_usage = ((total_time_sec - prev_cpu_time) / time_delta) * 100
            cpu_pct_str = f"{max(0.0, cpu_usage):.1f}%"

        prev_cpu_time = total_time_sec
        prev_calc_time = now
        return f"{used_mb} MB / {config.MAX_ALLOCATED_RAM_MB} MB ({pct:.1f}%)", cpu_pct_str
    except Exception:
        return f"0 MB / {config.MAX_ALLOCATED_RAM_MB} MB (0%)", "0.0%"

async def query_minecraft_status():
    try:
        server = await JavaServer.async_lookup("127.0.0.1:25565", timeout=2.0)
        return await server.async_status()
    except Exception:
        return None
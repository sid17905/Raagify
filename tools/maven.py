"""Optional portable Maven launcher; normal installations can use mvn directly."""

from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
maven = root / "tools" / "apache-maven-3.9.9"
java_home = Path(os.environ.get("JAVA_HOME", r"C:\Program Files\Java\jdk-21.0.10"))
jar = next((maven / "boot").glob("plexus-classworlds-*.jar"))
command = [
    str(java_home / "bin" / "java.exe"),
    f"-Dmaven.home={maven}",
    f"-Dclassworlds.conf={maven / 'bin' / 'm2.conf'}",
    f"-Dmaven.multiModuleProjectDirectory={root}",
    f"-Dmaven.repo.local={root / '.cache' / 'm2'}",
    "-Dfile.encoding=UTF-8",
    "-classpath",
    str(jar),
    "org.codehaus.plexus.classworlds.launcher.Launcher",
    "--batch-mode",
    "--no-transfer-progress",
    *sys.argv[1:],
]
sys.exit(subprocess.call(command))

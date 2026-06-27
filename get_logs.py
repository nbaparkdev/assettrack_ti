import subprocess

try:
    result = subprocess.run(
        ["docker", "compose", "logs", "-n", "40", "web"],
        capture_output=True,
        text=True,
        cwd="/home/humberto/Aplicativos/assettrack_ti"
    )
    with open("web_logs_tmp.txt", "w") as f:
        f.write(result.stdout)
        f.write("\n--- ERROR ---\n")
        f.write(result.stderr)
    print("Logs salvos com sucesso.")
except Exception as e:
    print(f"Erro ao salvar logs: {e}")

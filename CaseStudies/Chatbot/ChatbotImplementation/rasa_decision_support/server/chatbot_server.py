#!/usr/bin/env python3

import os
import subprocess
import time
import socket
import shutil

# === Configuration ===
RASA_BIN = "Set path to rasa executable, e.g.: ~/virtualenvs/rasa_env/bin/rasa"
WORKFLOWS_FILENAME = "active.workflowspec"
ADAPT_DIR_NAME = "sleec-adapt"
WORKFLOW_BASE_DIR = "workflows/workflow_base"
JAR_PATH = os.path.join(ADAPT_DIR_NAME, "agent-adaption.jar")

# === UI Header ===
print("\033]0;🔧 Chatbot Server\007")
print("=" * 60)
print("🤖  ADAPTIVE CHATBOT SERVER INITIALIZED")
print("=" * 60)


def find_rasa_project_root(start_path):
    """Locate project root containing domain.yml and actions folder."""
    path = os.path.abspath(start_path)
    while path != "/":
        if (
            os.path.isdir(os.path.join(path, "actions"))
            and os.path.isfile(os.path.join(path, "domain.yml"))
        ):
            return path
        path = os.path.dirname(path)
    return None


# === Detect and prepare paths ===
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = find_rasa_project_root(current_dir)

if not project_root:
    print("❌ Could not find Rasa project root (missing actions/ or domain.yml). Exiting.")
    exit(1)

print("📁 Project root detected ✅")
os.chdir(project_root)

# === Start Rasa action server ===
print("🚀 Starting Rasa action server in background...")
subprocess.Popen(
    [RASA_BIN, "run", "actions", "--quiet"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)


def wait_for_port(host="localhost", port=5055, timeout=10):
    """Wait for the action server to be ready."""
    print(f"⏳ Waiting for action server on {host}:{port}...", end="", flush=True)
    for _ in range(timeout):
        try:
            with socket.create_connection((host, port), timeout=2):
                print(" ✅ Ready.")
                return True
        except Exception:
            print(".", end="", flush=True)
            time.sleep(1)
    print(" ❌ Timeout.")
    return False


wait_for_port()

# === Folder setup ===
WORKFLOWS_DIR = os.path.join(project_root, "workflows")
WORKFLOW_BASE = os.path.join(WORKFLOWS_DIR, "workflow_base")
ADAPT_DIR = os.path.join(project_root, ADAPT_DIR_NAME)
os.makedirs(ADAPT_DIR, exist_ok=True)

# === Clean previous session files ===
for f in os.listdir(ADAPT_DIR):
    if (
        (f.endswith(".sleec") and f != "universal_rules.sleec") or
        f == "client.info" or
        f == "active.workflowspec" or
        f == "Chatbot.workflowspec"
    ):
        os.remove(os.path.join(ADAPT_DIR, f))

# === Load and apply base workflow + universal rule ===
base_workflow = None
base_rule = None

for f in os.listdir(WORKFLOW_BASE):
    if f.endswith(".workflowspec"):
        base_workflow = os.path.join(WORKFLOW_BASE, f)
    elif f.endswith(".sleec"):
        base_rule = os.path.join(WORKFLOW_BASE, f)

if not base_workflow:
    print("❌ No base workflow found in workflow_base.")
    exit(1)

# Copy base workflow and rules to sleec-adapt
shutil.copy(base_workflow, os.path.join(ADAPT_DIR, "Chatbot.workflowspec"))
if base_rule:
    shutil.copy(base_rule, os.path.join(ADAPT_DIR, "universal_rules.sleec"))

# === Run initial adaptation ===
print("🔄 Loading workflow")
os.chdir(ADAPT_DIR)

if base_rule:
    print("✅ Found common SLEEC rules")

    sdkman_init = os.path.expanduser("~/.sdkman/bin/sdkman-init.sh")
    if os.path.exists(sdkman_init):
        java_cmd = f'''
            source "{sdkman_init}" && \
            sdk use java 11.0.20-tem > /dev/null && \
            java -jar agent-adaption.jar "Chatbot.workflowspec" "universal_rules.sleec" "active"
        '''
        subprocess.run(
            ["bash", "-c", java_cmd],
            cwd=ADAPT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        subprocess.run(
            ["java", "-jar", "agent-adaption.jar", "Chatbot.workflowspec", "universal_rules.sleec", "active"],
            cwd=ADAPT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
else:
    shutil.copy("Chatbot.workflowspec", "active.workflowspec")

# Copy adapted workflow to /workflows
final_output = os.path.join(ADAPT_DIR, "active.workflowspec")
if os.path.exists(final_output):
    shutil.copy(final_output, os.path.join(WORKFLOWS_DIR, WORKFLOWS_FILENAME))
    print("🧠 Workflow adapted")
else:
    print("❌ Adaptation failed: active.workflowspec not produced.")
    exit(1)

# === Initialize monitoring ===
active_path = os.path.join(WORKFLOWS_DIR, WORKFLOWS_FILENAME)
previous_workflow_hash = None
if os.path.exists(active_path):
    with open(active_path, "rb") as f:
        previous_workflow_hash = hash(f.read())

print("📡 Waiting for client conversations...")
print("-" * 48)

# === Monitor for client updates ===
seen_clients = set()

try:
    while True:
        # Look for client marker
        marker_path = os.path.join(ADAPT_DIR, "client.info")
        if os.path.exists(marker_path):
            with open(marker_path, "r") as f:
                client_name = f.read().strip()

            if client_name and client_name not in seen_clients:
                seen_clients.add(client_name)
                print(f"\n📥 Connection requested at {time.strftime('%H:%M:%S')}")
                print(f"\n👤 Connected '{client_name}'")

                # Check for user SLEEC rules (excluding universal)
                user_rules = sorted(
                    f for f in os.listdir(ADAPT_DIR)
                    if f.endswith(".sleec") and f != "universal_rules.sleec"
                )

                if user_rules:
                    print(f"✅ Found '{client_name}' SLEEC rules")
                    #print(f"🔍 Will apply rules (in order): {user_rules}")

                    # --- (A) Build a fresh base for THIS client: Chatbot + universal ---
                    base_input  = "Chatbot.workflowspec"              # guaranteed present in ADAPT_DIR
                    base_rule   = "universal_rules.sleec"             # guaranteed present in ADAPT_DIR (from startup)
                    base_output = f"base_{client_name}"               # jar will emit base_<client_name>.workflowspec

                    sdkman_init = os.path.expanduser("~/.sdkman/bin/sdkman-init.sh")
                    if os.path.exists(sdkman_init):
                        cmd = (
                            f'source "{sdkman_init}" && '
                            f'sdk use java 11.0.20-tem > /dev/null && '
                            f'java -jar agent-adaption.jar "{base_input}" "{base_rule}" "{base_output}"'
                        )
                        res_base = subprocess.run(["bash", "-c", cmd], cwd=ADAPT_DIR,
                                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        res_base = subprocess.run(
                            ["java", "-jar", JAR_PATH, base_input, base_rule, base_output],
                            cwd=ADAPT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                        )

                    produced_base = os.path.join(ADAPT_DIR, f"{base_output}.workflowspec")
                    if res_base.returncode != 0 or not os.path.exists(produced_base):
                        print(f"❌ Could not create base for '{client_name}' (Chatbot + universal)")
                        # do NOT overwrite the active; keep current one
                        # optionally: continue to next loop iteration
                        continue

                    # --- (B) Apply user rules sequentially on top of the fresh base ---
                    current_input = f"{base_output}.workflowspec"     # start from the freshly-created base
                    success = True

                    for idx, rule in enumerate(user_rules):
                        out_stem = f"temp_{client_name}_{idx}"        # jar will produce temp_<client>_<i>.workflowspec

                        if os.path.exists(sdkman_init):
                            cmd = (
                                f'source "{sdkman_init}" && '
                                f'sdk use java 11.0.20-tem > /dev/null && '
                                f'java -jar agent-adaption.jar "{current_input}" "{rule}" "{out_stem}"'
                            )
                            res_rule = subprocess.run(["bash", "-c", cmd], cwd=ADAPT_DIR,
                                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        else:
                            res_rule = subprocess.run(
                                ["java", "-jar", JAR_PATH, current_input, rule, out_stem],
                                cwd=ADAPT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                            )

                        produced = os.path.join(ADAPT_DIR, f"{out_stem}.workflowspec")
                        if res_rule.returncode != 0 or not os.path.exists(produced):
                            print(f"❌ Adaptation failed while applying rule '{rule}'")
                            success = False
                            break

                        current_input = f"{out_stem}.workflowspec"    # chain to next

                    # --- (C) Publish result if all rules succeeded ---
                    if success and os.path.exists(os.path.join(ADAPT_DIR, current_input)):
                        final_active = os.path.join(ADAPT_DIR, "active.workflowspec")
                        # Avoid SameFileError if current_input already is active.workflowspec
                        if os.path.abspath(os.path.join(ADAPT_DIR, current_input)) != os.path.abspath(final_active):
                            shutil.copy(os.path.join(ADAPT_DIR, current_input), final_active)

                        shutil.copy(final_active, os.path.join(WORKFLOWS_DIR, WORKFLOWS_FILENAME))
                        print(f"🧠 Workflow adapted for '{client_name}'")
                    else:
                        print(f"⚠️ Adaptation incomplete for '{client_name}' — workflow unchanged.")

                    # --- (D) Cleanup temps for this client only ---
                    for f in os.listdir(ADAPT_DIR):
                        if f.startswith(f"temp_{client_name}_") or f == f"base_{client_name}.workflowspec":
                            try:
                                os.remove(os.path.join(ADAPT_DIR, f))
                            except Exception:
                                pass
                else:
                    # (No rules branch stays as you added earlier: regenerate base active)
                    chat_spec = os.path.join(ADAPT_DIR, "Chatbot.workflowspec")
                    uni_rule  = os.path.join(ADAPT_DIR, "universal_rules.sleec")
                    final_active = os.path.join(ADAPT_DIR, "active.workflowspec")

                    # Rebuild base active from Chatbot + universal for rule-less clients
                    if os.path.exists(sdkman_init):
                        cmd = (
                            f'source "{sdkman_init}" && '
                            f'sdk use java 11.0.20-tem > /dev/null && '
                            f'java -jar agent-adaption.jar "Chatbot.workflowspec" "universal_rules.sleec" "active"'
                        )
                        res = subprocess.run(["bash", "-c", cmd], cwd=ADAPT_DIR,
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        res = subprocess.run(
                            ["java", "-jar", JAR_PATH, "Chatbot.workflowspec", "universal_rules.sleec", "active"],
                            cwd=ADAPT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                        )

                    if res.returncode == 0 and os.path.exists(final_active):
                        shutil.copy(final_active, os.path.join(WORKFLOWS_DIR, WORKFLOWS_FILENAME))
                        print(f"ℹ️  No SLEEC rules found for '{client_name}'")
                    else:
                        print(f"❌ Could not regenerate base workflow for '{client_name}'")
                # Clean up marker file so another client can reuse it
                os.remove(marker_path)

        time.sleep(2)

except KeyboardInterrupt:
    print("\n👋 Server interrupted. Shutting down gracefully.")
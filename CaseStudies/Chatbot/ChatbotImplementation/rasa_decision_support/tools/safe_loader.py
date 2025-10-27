import importlib.util
import os
import sys

def load_workflow_only():
    """
    Dynamically import load_workflow() from actions/workflow_loader.py
    without importing rasa_sdk or the rest of actions/.
    """
    here = os.path.dirname(__file__)
    wf_path = os.path.abspath(os.path.join(here, "..", "actions", "workflow_loader.py"))
    if not os.path.exists(wf_path):
        raise FileNotFoundError(f"Could not find workflow_loader.py at {wf_path}")

    spec = importlib.util.spec_from_file_location("workflow_loader", wf_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["workflow_loader"] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "load_workflow"):
        raise AttributeError("workflow_loader.py does not define load_workflow()")
    return module.load_workflow
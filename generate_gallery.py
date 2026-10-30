import os
import sys

# Ensure base site-packages are accessible
for p in [r"D:\Nimish_project\Lib\site-packages", os.path.join(os.getcwd(), "venv_312", "Lib", "site-packages")]:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

from skills.diagram_engine import (
    generate_system_architecture_diagram,
    generate_ml_lifecycle_diagram,
    generate_neural_network_diagram,
    generate_confusion_matrix_diagram,
    generate_decision_tree_diagram,
    generate_flowchart_diagram
)

gallery_dir = os.path.join(os.getcwd(), "Devpost_Gallery")
os.makedirs(gallery_dir, exist_ok=True)

print(f"Generating Devpost gallery images to: {gallery_dir}")

f1 = os.path.join(gallery_dir, "01_System_Architecture_Overview.png")
generate_system_architecture_diagram(f1, title="MAYA Cyber Companion OS")
print(f"Saved: {f1}")

f2 = os.path.join(gallery_dir, "02_Machine_Learning_Lifecycle_Pipeline.png")
generate_ml_lifecycle_diagram(f2)
print(f"Saved: {f2}")

f3 = os.path.join(gallery_dir, "03_Deep_Neural_Network_Topology.png")
generate_neural_network_diagram(f3)
print(f"Saved: {f3}")

f4 = os.path.join(gallery_dir, "04_Model_Evaluation_Confusion_Matrix.png")
generate_confusion_matrix_diagram(f4)
print(f"Saved: {f4}")

f5 = os.path.join(gallery_dir, "05_Decision_Tree_Architecture.png")
generate_decision_tree_diagram(f5)
print(f"Saved: {f5}")

f6 = os.path.join(gallery_dir, "06_Algorithmic_Execution_Workflow.png")
generate_flowchart_diagram(f6, title="Cognitive Intent Dispatch Workflow")
print(f"Saved: {f6}")

print("All 6 high-resolution gallery images generated successfully!")

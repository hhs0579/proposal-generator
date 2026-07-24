import shutil
import os

source_dir = "C:/Users/Esser/Desktop/esser dev/proposal-generator"
temp_dir = "C:/Users/Esser/Desktop/esser dev/temp_deploy"

# Clean up temp if exists
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)

# Copy everything EXCEPT node_modules and venv
def ignore_patterns(path, names):
    ignored = set()
    if 'node_modules' in names: ignored.add('node_modules')
    if 'venv' in names: ignored.add('venv')
    if '__pycache__' in names: ignored.add('__pycache__')
    return ignored

shutil.copytree(source_dir, temp_dir, ignore=ignore_patterns)

# Zip it
zip_path = "C:/Users/Esser/Desktop/proposal-generator-deploy"
shutil.make_archive(zip_path, 'zip', temp_dir)

# Clean up temp
shutil.rmtree(temp_dir)

print(f"Successfully created {zip_path}.zip")


import os

def generate_manifest(base_path='.'):
    manifest = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.py'):
                manifest.append(os.path.relpath(os.path.join(root, file), base_path))
    with open('module_manifest.txt', 'w') as f:
        for item in sorted(manifest):
            f.write(item + '\n')

if __name__ == '__main__':
    generate_manifest()

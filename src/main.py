from src.helper import generate_pages_recursive
import os
import shutil
import sys


def main():
    basepath = sys.argv if sys.argv else "/"
    if os.path.exists("public"):
        shutil.rmtree("public")
    os.mkdir("public")
    _copy_dir_file("static", "public")
    generate_pages_recursive("content", "template.html", "docs./", basepath)


def _copy_dir_file(src, dst):
    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)
        if os.path.isfile(src_path):
            shutil.copy(src_path, dst_path)
            print(f"File {src_path} is copied to {dst_path}")
        if os.path.isdir(src_path):
            os.makedirs(dst_path, exist_ok=True)
            print(f"Dictionary {dst_path} is created")
            _copy_dir_file(src_path, dst_path)


if __name__ == "__main__":
    main()

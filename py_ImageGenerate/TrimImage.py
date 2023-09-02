import os
import sys
from PIL import Image, UnidentifiedImageError
import shutil
import json

ABS_FILE_DIR = os.path.dirname(__file__)
ABS_FILE_PATH = os.path.abspath(__file__)
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

CONFIG_DIR = "Configs"
CONFIG_FILE = "config.json" # -> JSON を使用する場合
#CONFIG_FILE = "config.yaml" # -> YAML を使用する場合
CONFIG_FILE_PATH = os.path.join(ROOT_DIR, CONFIG_DIR, CONFIG_FILE)

TMP_DIR = "tmp"
TMP_FILE = "Notion_Pages.json"
TMP_FILE_PATH = os.path.join(ROOT_DIR, TMP_DIR, TMP_FILE)

IMAGE_DIR = "images"
IMAGE_DIR_PATH = os.path.join(ROOT_DIR, TMP_DIR, IMAGE_DIR)
os.makedirs(IMAGE_DIR_PATH, exist_ok=True)
TRIMMED_DIR = "trim_img"
TRIMMED_DIR_PATH = os.path.join(ROOT_DIR, TMP_DIR, TRIMMED_DIR)
os.makedirs(TRIMMED_DIR_PATH, exist_ok=True)
BIN_DIR = "bin_img"
BIN_DIR_PATH = os.path.join(ROOT_DIR, TMP_DIR, BIN_DIR)
os.makedirs(BIN_DIR_PATH, exist_ok=True)

META_FILE = "metadata.txt"

LOG_DIR = "log"
LOG_FILE = "debug.log"
LOG_FILE_PATH = os.path.join(ROOT_DIR, LOG_DIR, LOG_FILE)


# トリミング後の縦横比率
WH_RATIO = 40 / 21
""" 
def main(argv):
    for tgt in argv[1:]:
        if os.path.isdir(tgt):
            for f in os.listdir(tgt):
                tp = os.path.join(tgt, f)
                if not os.path.isdir(tp):
                    trim_image(tp)
        else:
            trim_image(tgt)

def trim_image(fp):
    try:
        img = Image.open(fp)
        img_ratio = img.width / img.height
        print(img_ratio, WH_RATIO)
        input()

        if img_ratio < WH_RATIO:
            # 画像の縦横比がトリミング後の比率よりも大きい場合、上下をトリミング
            new_height = int(img.width / WH_RATIO)
            upper = (img.height - new_height) // 2
            lower = img.height - upper
            img = img.crop((0, upper, img.width, lower))
        else:
            # 画像の縦横比がトリミング後の比率よりも小さい場合、左右をトリミング
            new_width = int(img.height * WH_RATIO)
            left = (img.width - new_width) // 2
            right = img.width - left
            img = img.crop((left, 0, right, img.height))

        dst_dir = os.path.join(os.path.dirname(fp), 'trimmed')

        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)

        img.save(os.path.join(dst_dir, os.path.basename(fp)))

    except UnidentifiedImageError:
        pass
    except FileNotFoundError:
        pass

if __name__ == '__main__':
    main(sys.argv)
 """

def execute_trim(src_file, dst_dir):
  try:
    img = Image.open(src_file)
    img_ratio = img.width / img.height
    #print(img_ratio, WH_RATIO)
    #input()

    if img_ratio < WH_RATIO:
        # 画像の縦横比がトリミング後の比率よりも大きい場合、上下をトリミング
      new_height = int(img.width / WH_RATIO)
      upper = (img.height - new_height) // 2
      lower = img.height - upper
      img = img.crop((0, upper, img.width, lower))
    else:
        # 画像の縦横比がトリミング後の比率よりも小さい場合、左右をトリミング
      new_width = int(img.height * WH_RATIO)
      left = (img.width - new_width) // 2
      right = img.width - left
      img = img.crop((left, 0, right, img.height))

    #dst_dir = os.path.join(os.path.dirname(path), 'trimmed')

    #os.makedirs
    #if not os.path.exists(dst_dir):
    #    os.mkdir(dst_dir)
    dst_path = os.path.join(dst_dir, os.path.basename(src_file))
    print(dst_path)

    img.save(dst_path)

  except UnidentifiedImageError:
    pass
  except FileNotFoundError:
    pass

def move_bin(src_dir_path):
  #print(src_dir_path)
  dst_dir_path = os.path.join(BIN_DIR_PATH, os.path.basename(src_dir_path))
  #print(dst_dir_path)
  os.makedirs(dst_dir_path, exist_ok=True)
  for f in os.listdir(src_dir_path):
    if os.path.isdir(f):
      continue
    shutil.move(os.path.join(src_dir_path, f), dst_dir_path)

def delete_dir(dir_path):
  shutil.rmtree(dir_path)
  
def read_NotionObj() -> list:
  with open(TMP_FILE_PATH, mode='r') as f:
    data = json.load(f)
  return data

def write_NotionObj(data):
  data["checkpoint"] = 4
  with open(TMP_FILE_PATH, mode='w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    #data = json.load(f)

def trim_image():
  for target in os.listdir(IMAGE_DIR_PATH):
    #print(IMAGE_DIR_PATH)
    #print(target)
    target_trim_dir = os.path.join(TRIMMED_DIR_PATH, target)
    target_image_dir = os.path.join(IMAGE_DIR_PATH, target)
    #print(os.path.isdir(target_image_dir))

    if not os.path.isdir(target_image_dir):
      print(f"{target} is not a directory, skipping the process...")
      continue
    print(f"Trimming images under {os.path.basename(target)}...")

    #target_image_dir = os.path.join(IMAGE_DIR_PATH, target)
    os.makedirs(target_trim_dir, exist_ok=True)
    for img in os.listdir(target_image_dir):
      img_path = os.path.join(target_image_dir, img)

      if os.path.isdir(img_path):
        continue
      
      execute_trim(img_path, target_trim_dir)
    move_bin(target_image_dir)
    delete_dir(target_image_dir)
  Notion_Obj = read_NotionObj()
  write_NotionObj(Notion_Obj)


    
  #input()
  """ 
  for tgt in argv[1:]:
      if os.path.isdir(tgt):
          for f in os.listdir(tgt):
        tp = os.path.join(tgt, f)
        if not os.path.isdir(tp):
          trim_image(tp)
    else:
      trim_image(tgt)
 """

def main():
  trim_image()

if __name__ == '__main__':
  main()

import os
import shutil
from argparse import ArgumentParser
from selenium import webdriver
from selenium.webdriver.common.by import By
import subprocess
from time import sleep
import datetime
import re
from concurrent.futures import ThreadPoolExecutor
import json
import itertools
import glob
import requests
import json
import base64
import os

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

TRIMMED_DIR = "trim_img"
TRIMMED_DIR_PATH = os.path.join(ROOT_DIR, TMP_DIR, TRIMMED_DIR)
os.makedirs(TRIMMED_DIR_PATH, exist_ok=True)

META_FILE = "metadata.txt"

LOG_DIR = "log"
LOG_FILE = "debug.log"
LOG_FILE_PATH = os.path.join(ROOT_DIR, LOG_DIR, LOG_FILE)

IMAGE_CNT = 5

def read_config(arg):
  with open(CONFIG_FILE_PATH, mode='r') as f:
    data = json.load(f)
  WP_Auth = data["py_WordPress"].keys()
  if arg in WP_Auth:
    return data["py_WordPress"][arg]
  else:
    exit(f"read_config エラー: 引数には {', '.join(WP_Auth)} のいずれかのみ有効")
  
URL = read_config("URL")
USER = read_config("User")
PASSWORD = read_config("Key")

PATH_POSTS = 'wp-json/wp/v2/posts/'
PATH_MEDIA = 'wp-json/wp/v2/media/'

# Create WP Connection
CREDENTIALS = f"{USER}:{PASSWORD}"
# Encode the connection of your website
TOKEN = base64.b64encode(CREDENTIALS.encode())
# Prepare the header of our request
HEADERS = {
  'Authorization': 'Basic ' + TOKEN.decode('utf-8')
  }

def read_json():
  with open(TMP_FILE_PATH, mode='r') as f:
    s = json.load(f)
    #print(s)
  return s

def json_to_IMAGE(dict_data:dict) -> list:
  data_list = []
  elements = dict_data["elements"]
  for ele in elements:
    data = {
      'Title': ele["Title"],
      'Images': ele["Images"],
    }
    data_list.append(data)
  return data_list

def get_file_type(filename):
  # Content-Typeの指定
  print(filename)
  file_extention = filename.split('.')[-1].lower()
  if file_extention in ['jpg', 'jpeg']:
      contentType = 'image/jpg'
  elif file_extention == 'png':
      contentType = 'image/png'
  elif file_extention == 'gif':
      contentType = 'image/gif'
  elif file_extention == 'bmp':
      contentType = 'image/bmp'
  elif file_extention == 'mp4':
      contentType = 'movie/mp4'
  else:
      print(f'not supported [{file_extention}]')
      exit()
  return contentType

def get_headers():
  pass

def get_file_path(title, num):
  return os.path.join(TRIMMED_DIR_PATH, title, num)

def upload_image(images:list) -> dict:
  api_url = f'{URL}{PATH_MEDIA}'
  for image in images:
    print(image)
    WPID = []
    for i in range(len(image['Images'])):
      file_path = get_file_path(image['Title'], image['Images'][i])
      file_name = os.path.basename(file_path)
      file_type = get_file_type(file_name)
      data = {
        "slug": file_name.split('.')[-2],
        "title": file_name.split('.')[-2],
        }
      headers = {
        'Authorization': 'Basic ' + TOKEN.decode('utf-8'),
        }
      
      with open(file_path, mode='rb') as f:
        files = {'file': (file_path, f, file_type)}  # ファイル名とコンテンツタイプを設定
        res = requests.post(url=api_url, headers=headers, files=files, data=data)
      if res.ok:
        print(f"メディアの追加 成功 code:{res.status_code}")
        res_content = json.loads(res.content.decode('utf-8'))
        WPID.append(res_content['id'])
      else:
        error_msg = json.loads(res.content.decode('utf-8'))
        print(f"メディアの追加 失敗 code:{res.status_code} reason:{res.reason} msg:{error_msg}")

    with open(TMP_FILE_PATH, mode='r') as f:
      data = json.load(f)
    for d in data["elements"]:
      if d["Title"] == image["Title"]:
        d["ImageWPID"] = WPID

    data["checkpoint"] = 5
    with open(TMP_FILE_PATH, mode='w') as f:
      json.dump(data, f, indent=2, ensure_ascii=False)
  return

def wp_create_post(posts:list) -> dict:
  api_url = f'{URL}{PATH_POSTS}'
  for post in posts:
    res = requests.post(api_url, headers=HEADERS, json=post)
    if res.ok:
      print(f"投稿の追加 成功 code:{res.status_code}")
    else:
      error_msg = json.loads(res.content.decode('utf-8'))
      print(f"投稿の追加 失敗 code:{res.status_code} reason:{res.reason} msg:{error_msg['message']}")

def delete_sub_dir(dir_path):
  shutil.rmtree(dir_path)
  os.makedirs(dir_path)

def post_images():
  notion_data = read_json()
  data_for_IMAGE = json_to_IMAGE(notion_data)
  upload_image(data_for_IMAGE)
  delete_sub_dir(TRIMMED_DIR_PATH)

def main():
  post_images()
  pass

if __name__ == "__main__":
  main()

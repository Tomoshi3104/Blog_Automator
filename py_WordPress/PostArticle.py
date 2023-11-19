import requests
import json
import base64
import os
from googletrans import Translator
"https://developer.wordpress.org/rest-api/reference/posts/"

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

META_FILE = "metadata.txt"

LOG_DIR = "log"
LOG_FILE = "debug.log"
LOG_FILE_PATH = os.path.join(ROOT_DIR, LOG_DIR, LOG_FILE)

HEADTAIL_PUDDING = '\n'
INNER_PUDDING = '\n\n\n\n'

"Notion のコラム、Status の項目一覧"
STATUS_NO = "NotAssigned"
STATUS_GO = "AutoQueue"
STATUS_ONGOING = "PostQueue"
STATUS_AWAIT = "ReviewAwaiting"
STATUS_FIX = "ChangeQueue"
STATUS_END = "Confirmed"

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
  return s

def html_mixer(data):
  print(data)
  mixture = []
  for i in range(len(data)):
    tag = data[i]["html_type"]
    if i == 0:
      tag[0] = f"{HEADTAIL_PUDDING}{tag[0]}"
    if i != len(data):
      tag[1] = f"{tag[1]}{INNER_PUDDING}"
    elif i == len(data):
      tag[1] = f"{tag[1]}{HEADTAIL_PUDDING}"
    string = data[i]["string"]
    mixture.append(f"{tag[0]}{string}{tag[1]}")
  return mixture

def json_to_POST(dict_data:dict) -> list:
  data_list = []
  elements = dict_data["elements"]
  for ele in elements:
    data = {
      'title': ele["Title"],
      'status': 'private',  # publish, draft, private, pending
      'content': '\n'.join(ele["Contents"]), ###整形が必要
      'categories': [], #[5],
      'tags': [], #[189, 148],
      'slug': jp_en_translate(ele['Title']),
      'featured_media': ele['ImageWPID'][0]
    }
    data_list.append(data)
  return data_list

def jp_en_translate(string):
  translator = Translator()
  if not (string.isalnum() and string.isascii()):
    string = translator.translate(string, dest='en').text
  return string

def wp_create_post_test() -> dict:
  post = {
    'title': 'Hello World',
    'status': 'draft',  # publish',
    'content': 'テスト',
    'categories': [5],
    'tags': [189, 148],
    'slug': 'pre_open',
  }

  api_url = f'{URL}{PATH_POSTS}'
  res = requests.post(api_url, headers=HEADERS, json=post)
  res_dict = res.json()
  with open("./test_post.json", mode='w') as f:
    json.dump(res_dict, f, indent=2, ensure_ascii=False)
  if res.ok:
    print(f"投稿の追加 成功 code:{res.status_code}")
    
    return json.loads(res.text)
  else:
    error_msg = json.loads(res.content.decode('utf-8'))
    print(f"投稿の追加 失敗 code:{res.status_code} reason:{res.reason} msg:{error_msg['message']}")        
    return {}

def wp_create_post(posts:list) -> dict:
  api_url = f'{URL}{PATH_POSTS}'
  post_info = {}
  for post in posts:
    print(f"Article Title: {post['title']}")
    res = requests.post(api_url, headers=HEADERS, json=post)
    if res.ok:
      res_content = json.loads(res.content.decode('utf-8'))
      print(f"投稿の追加 成功 code:{res.status_code}")
      
      post_info[post['title']] = {
        'ID': res_content['id'],
        'URL': res_content['link'],
        }
      
    else:
      error_msg = json.loads(res.content.decode('utf-8'))
      print(f"投稿の追加 失敗 code:{res.status_code} reason:{res.reason} msg:{error_msg['message']}")
  return post_info

# Define Function to Call the Posts Endpoint
def get_posts():
  ID = 346
  api_url = f'{URL}{PATH_POSTS}{ID}'
  data = {
  }
  response = requests.get(api_url, headers=HEADERS, json=data)
  print(response)
  res = response.json()
  with open("./sample.json", mode='w') as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
  return response.json()
 
def get_images():
  api_url = f'{URL}{PATH_MEDIA}'
  data = {}
  response = requests.get(api_url, headers=HEADERS, json=data)
  print(response)
  res = response.json()
  with open("./sample_media.json", mode='w') as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
  return response.json()

def erase_json():
  os.remove(TMP_FILE_PATH)
  pass

def update_json(json_data:dict, reflection:dict):
  print(json_data, "==============================", reflection, sep='\n')
  input("update_json")
  for ele in json_data['elements']:
    if ele['Title'] in reflection.keys():
      ele['WPID'] = reflection[ele['Title']]['ID']
      ele['URL'] = reflection[ele['Title']]['URL']
      ele['Status'] = STATUS_ONGOING
  with open(TMP_FILE_PATH, mode='w') as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)

  pass

def post_articles():
  notion_data = read_json()
  data_for_POST = json_to_POST(notion_data)
  wp_create_post(data_for_POST)
  
  notion_data["checkpoint"] = 0
  with open(TMP_FILE_PATH, mode='w') as f:
    json.dump(notion_data, f, indent=2, ensure_ascii=False)

def upload_images():
  pass

def main():
  post_articles()

if __name__ == "__main__":
  main()

import requests
import json
import base64
import os
from googletrans import Translator
"https://developer.wordpress.org/rest-api/reference/posts/"
#URL = "https://glossary.web3-nft-blockchain.com/"
#EMAIL = "minami0810sts@gmail.com"
#USER = "Satoshi"
#PASSWORD = "x9ZW#FL8TRuJkQUbruYlPRgB"
#PASSWORD = {
#  Python_API:CmGA tJGt iu8S 32q9 QIhJ F4Pu
#}

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
""" AUTH = {
  'USER': 'Satoshi',
  'KEY': 'CmGA tJGt iu8S 32q9 QIhJ F4Pu'
  } """

# Create WP Connection
CREDENTIALS = f"{USER}:{PASSWORD}"
# Encode the connection of your website
TOKEN = base64.b64encode(CREDENTIALS.encode())
# Prepare the header of our request
HEADERS = {
  'Authorization': 'Basic ' + TOKEN.decode('utf-8')
  }
""" 
def html_converter(element):
  converter = {
    "h1": ['<h1 class=\"wp-block-heading\">', '</h1>'],
    "h2": ['<h2 class=\"wp-block-heading\">', '</h2>'],
    "h3": ['<h3 class=\"wp-block-heading\">', '</h3>'],
    "p": ['<p>', '</p>']
    }

  if element not in converter:
    return element
  return converter[element]
 """
def read_json():
  with open(TMP_FILE_PATH, mode='r') as f:
    s = json.load(f)
    #print(s)
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
  #input("stop")
""" 
def html_converter(data):
  #input(data)
  print(data)
  input(data["Contents"])
  mixture = []
  for i in range(len(data)):
    #tag = data[i]["html_type"]
    if i == 0:
      tag[0] = f"{HEADTAIL_PUDDING}{tag[0]}"
    if i != len(data):
      tag[1] = f"{tag[1]}{INNER_PUDDING}"
    elif i == len(data):
      tag[1] = f"{tag[1]}{HEADTAIL_PUDDING}"
    string = data[i]["string"]
    mixture.append(f"{tag[0]}{string}{tag[1]}")
  return mixture
  #input("stop")
 """
"""  
def json_to_IMAGE(dict_data:dict) -> list:
  data_list = []
  elements = dict_data["elements"]
  input(elements)
  for ele in elements:
    html_mix = "".join(html_converter(ele["Contents"]))
    #html_mix = "".join(html_mixer(ele["Contents"]))
    data = {
      'title': ele["Title"],
      'status': 'publish',  # publish, draft
      'content': html_mix, ###整形が必要
      'categories': [], #[5],
      'tags': [], #[189, 148],
      'slug': ele['Title'],
    }
    data_list.append(data)
  return data_list
 """
def json_to_POST(dict_data:dict) -> list:
  data_list = []
  elements = dict_data["elements"]
  #print(elements)
  for ele in elements:
    #print(ele)
    #html_mix = "".join(html_converter(ele["Contents"]))
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
  #print(api_url)
  res = requests.post(api_url, headers=HEADERS, json=post)
  #print(res.url)
  res_dict = res.json()
  with open("./test_post.json", mode='w') as f:
    json.dump(res_dict, f, indent=2, ensure_ascii=False)
  #print(res_dict["id"])
  #print(res.status_code)
  if res.ok:
    print(f"投稿の追加 成功 code:{res.status_code}")
    
    return json.loads(res.text)
  else:
    #print(f"投稿の追加 失敗 code:{res.status_code} reason:{res.reason} msg:{res.text}")
    #print(f"投稿の追加 失敗 code:{res.status_code} reason:{res.reason} msg:{res.content.decode('utf-8')}")
    error_msg = json.loads(res.content.decode('utf-8'))
    print(f"投稿の追加 失敗 code:{res.status_code} reason:{res.reason} msg:{error_msg['message']}")
        
    return {}

def wp_create_post(posts:list) -> dict:
  api_url = f'{URL}{PATH_POSTS}'
  #post_info = []
  post_info = {}
  for post in posts:
    print(f"Article Title: {post['title']}")
    res = requests.post(api_url, headers=HEADERS, json=post)
    #print(res)
    #print(res.status_code)
    if res.ok:
      res_content = json.loads(res.content.decode('utf-8'))
      #print(res_content)
      print(f"投稿の追加 成功 code:{res.status_code}")
      #input("success")
      #ID = res_content['id']
      #URL = res_content['link']
      """ 
      add_data = {
        post['title']: {
        'ID': res_content['id'],
        'URL': res_content['link'],
        }
      }
      post_info.append(add_data)
       """
      
      post_info[post['title']] = {
        'ID': res_content['id'],
        'URL': res_content['link'],
        }
      
      #return ID, URL
      #return json.loads(res.text)
    else:
      #print(f"投稿の追加 失敗 code:{res.status_code} reason:{res.reason} msg:{res.text}")
      #print(f"投稿の追加 失敗 code:{res.status_code} reason:{res.reason} msg:{res.content.decode('utf-8')}")
      error_msg = json.loads(res.content.decode('utf-8'))
      print(f"投稿の追加 失敗 code:{res.status_code} reason:{res.reason} msg:{error_msg['message']}")
      #return {}
  return post_info

# Define Function to Call the Posts Endpoint
def get_posts():
  #api_url = url + f'/posts'
  #api_url = 'https://glossary.web3-nft-blockchain.com/wp-admin/post.php?post=59&action=edit'
  #api_url = 'https://glossary.web3-nft-blockchain.com/2023/08/03/ar/'
  #api_url = 'https://glossary.web3-nft-blockchain.com/wp-admin/'
  ID = 346
  api_url = f'{URL}{PATH_POSTS}{ID}'
  data = {
    #'search': "61",
    #'include': 345

  }
  response = requests.get(api_url, headers=HEADERS, json=data)
  print(response)
  res = response.json()
  with open("./sample.json", mode='w') as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
  #print(response.text)
  #print(response.json())
  return response.json()
 
def get_images():
  api_url = f'{URL}{PATH_MEDIA}'
  data = {

  }
  response = requests.get(api_url, headers=HEADERS, json=data)
  print(response)
  res = response.json()
  with open("./sample_media.json", mode='w') as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
  #print(response.text)
  #print(response.json())
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
  #data_for_IMAGE = json_to_IMAGE(notion_data)
  data_for_POST = json_to_POST(notion_data)
  #print("====================================")
  #print(data_for_POST)
  #input("stop")
  #upload_images()
  wp_create_post(data_for_POST)
  
  notion_data["checkpoint"] = 0
  with open(TMP_FILE_PATH, mode='w') as f:
    json.dump(notion_data, f, indent=2, ensure_ascii=False)
  #reflection = wp_create_post(data_for_POST)
  #update_json(notion_data, reflection)

  """ 
  if erase_tmp:
    erase_json()
   """

def upload_images():
  pass

def main():
  post_articles()

if __name__ == "__main__":
  "get_posts() #For Debugging Purpose"
  #get_images()
  #input("stop")
  #wp_create_post_test()
  #exit()
  main()

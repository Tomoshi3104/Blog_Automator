import requests
import json
import os
import re

def get_auth():
  with open(CONFIG_FILE_PATH, mode='r') as f:
    data = json.load(f)
    db_id = data["py_Notion"]["ID"]
    key = data["py_Notion"]["Key"]
    return db_id, key

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

LOG_DIR = "log"
LOG_FILE = "debug.log"
LOG_FILE_PATH = os.path.join(ROOT_DIR, LOG_DIR, LOG_FILE)

"Notion のコラム、Status の項目一覧"
STATUS_NO = "NotAssigned"
STATUS_GO = "AutoQueue"
STATUS_ONGOING = "PostQueue"
STATUS_AWAIT = "ReveiwAwaiting"
STATUS_FIX = "ChangeQueue"
STATUS_END = "Confirmed"

DB_ID, Key = get_auth()

class Page():
  def __init__(self, ID, Title, FullForm, Prompts, Status) -> None:
    self.ID = ID
    self.Title = Title
    self.FullForm = FullForm
    self.Prompts = Prompts
    self.Status = Status
    self.Contents = []
    self.Key = Key
    self.Images = []
    return

  def get_all(self):
    info = {
      "ID": self.ID,
      "Title": self.Title,
      "FullForm": self.FullForm,
      "Prompts": self.Prompts,
      "Status": self.Status,
      "Contents": self.Contents,
      "Images": self.Images
    }
    return info
  
  def get_contents(self):
    bl_url = f"https://api.notion.com/v1/blocks/{self.ID}/children"
    headers = {
      "Accept": "application/json",
      "Notion-Version": "2022-06-28",
      "Authorization": "Bearer " + Key
  }
    bl_res = requests.get(bl_url, headers=headers)
    bl_dict = bl_res.json()

    "デバッグ時データ可視化用"
    with open("raw_Notion_Block.json", mode='w') as f:
      json.dump(bl_dict, f, indent=2, ensure_ascii=False)

    type_total = len(bl_dict["results"])
    for i in range(type_total):
      type_name = bl_dict["results"][i]["type"]
      if type_name not in ["paragraph", "heading_1", "heading_2", "heading_3"]:
        continue
      sub_type_total = len(bl_dict["results"][i][type_name]["rich_text"])
      
      for j in range(sub_type_total):
        sub_type_name = bl_dict["results"][i][type_name]["rich_text"][j]["type"]
        notion_type = bl_dict["results"][i]["type"]

        content = bl_dict["results"][i][type_name]["rich_text"][j][sub_type_name]["content"]
        html_type = self.get_html_tag(notion_type)
        html_data = {
          "html_type": html_type,
          "string": content
        }
        self.Contents.append(html_data)
    return self.Contents

  def get_html_tag(self, element):
    
    converter = {
      "heading_1": ['<h1 class=\"wp-block-heading\">', '</h1>'],
      "heading_2": ['<h2 class=\"wp-block-heading\">', '</h2>'],
      "heading_3": ['<h3 class=\"wp-block-heading\">', '</h3>'],
      "paragraph": ['<p>', '</p>']
    }
    if element not in converter:
      return element
    return converter[element]

def set_db_requests(db_id, key):
  data = {}
  url = "https://api.notion.com/v1/databases/" + db_id + "/query"
  headers = {
      "Accept": "application/json",
      "Notion-Version": "2022-06-28",
      "Authorization": "Bearer " + key
  }
  return requests.post(url, headers=headers, json=data)
  
def shape_Prompts(num, pages):
  if len(pages[num]["properties"]["Prompts"]["rich_text"]) == 0:
    return ""
  else:
    p = pages[num]["properties"]["Prompts"]["rich_text"][0]["plain_text"]
    return re.sub(r'\n|\r|\s', ' ', p)

def shape_FullForm(num, pages):
  if len(pages[num]["properties"]["FullForm"]["rich_text"]) == 0:
    return ""
  else:
    p = pages[num]["properties"]["FullForm"]["rich_text"][0]["plain_text"]
    return re.sub(r'\n|\r|\s', ' ', p)
    
def get_q_page(db):
  t_pages = []
  Page_LIST = db["results"]
  for i in range(len(Page_LIST)):
    Status = Page_LIST[i]["properties"]["Status"]["status"]["name"]
    if Status == STATUS_GO:
      ID = Page_LIST[i]["id"]
      Title = Page_LIST[i]["properties"]["Title"]["title"][0]["text"]["content"]
      FullForm = shape_FullForm(i, Page_LIST)
      Prompts = shape_Prompts(i, Page_LIST)
      t_pages.append(Page(ID, Title, FullForm, Prompts, Status))
  return t_pages

def get_pages():
  res_db = set_db_requests(DB_ID, Key)
  dict_db = res_db.json()
  Queue_INFO = {"elements":[]}
  PAGES = get_q_page(dict_db)
  for page in PAGES:
    "Enables when running Notion AI, Disable when running ChatGPT"
    Queue_INFO["elements"].append(page.get_all())

  Queue_INFO["checkpoint"] = 1
  with open(TMP_FILE_PATH, mode='w') as f:
    json.dump(Queue_INFO, f, indent=2, ensure_ascii=False)

def main():
  get_pages()

if __name__ == "__main__":
  main()



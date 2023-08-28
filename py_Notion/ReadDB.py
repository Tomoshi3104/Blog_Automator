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
#REL_FILE_DIR = f"./{os.path.relpath(ABS_FILE_DIR, ROOT_DIR)}"

#CACHE_FILE = "MS_Auth_Cookie.txt"
#CACHE_FILE_PATH = os.path.join(ABS_FILE_DIR, CACHE_FILE)

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



""" 
with open("./DATABASE.txt", mode='r') as f:
  d = {}
  s = f.readlines()
  for line in s:
    if line.split(":")[0].upper().strip(" ") == "ID":
      d["ID"] = line.split(":")[1].strip(" ").strip("\n")
    if line.split(":")[0].capitalize().strip(" ") == "Key":
      d["Key"] = line.split(":")[1].strip(" ").strip("\n")

"""
class Page():
  def __init__(self, ID, Title, FullForm, Prompts, Status) -> None:
  #"def __init__(self, ID, Title, CustomURL, Prompts, Status) -> None:"
    self.ID = ID
    self.Title = Title
    self.FullForm = FullForm
    #self.CustomURL = CustomURL
    self.Prompts = Prompts
    #self.URL = ""
    self.Status = Status
    #self.Tag = []
    self.Contents = []
    self.Key = Key
    self.Images = []
    return

  def get_all(self):
    info = {
      "ID": self.ID,
      "Title": self.Title,
      "FullForm": self.FullForm,
      #"CustomURL": self.CustomURL,
      "Prompts": self.Prompts,
      #"URL": self.URL,
      "Status": self.Status,
      #"Tag": self.Tag,
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
    #input("get_contents_block")
    "==============="

    type_total = len(bl_dict["results"])
    #print(f"type_total: {type_total}")
    #print("content head")
    for i in range(type_total):
      type_name = bl_dict["results"][i]["type"]
      if type_name not in ["paragraph", "heading_1", "heading_2", "heading_3"]:
        continue
      #print(f"type_name: {type_name}")
      sub_type_total = len(bl_dict["results"][i][type_name]["rich_text"])
      #print(f"sub_type_total: {sub_type_total}")
      
      for j in range(sub_type_total):
        sub_type_name = bl_dict["results"][i][type_name]["rich_text"][j]["type"]
        notion_type = bl_dict["results"][i]["type"]
        #print(f"sub_type_name: {sub_type_name}")

        content = bl_dict["results"][i][type_name]["rich_text"][j][sub_type_name]["content"]
        html_type = self.get_html_tag(notion_type)
        html_data = {
          "html_type": html_type,
          "string": content
        }
        self.Contents.append(html_data)
        #print(f"content: {content}")

        #print(type_name)
        #print(sub_type_name)
        #print(ele[0])
        #print(ele[1]["title"])
        
        #print(content)
    #print(self.Contents)
    return self.Contents

  def get_html_tag(self, element):
    
    converter = {
      "heading_1": ['<h1 class=\"wp-block-heading\">', '</h1>'],
      "heading_2": ['<h2 class=\"wp-block-heading\">', '</h2>'],
      "heading_3": ['<h3 class=\"wp-block-heading\">', '</h3>'],
      "paragraph": ['<p>', '</p>']
    }
    """ 
    converter = {
      "heading_1": "h1",
      "heading_2": "h2",
      "heading_3": "h3",
      "paragraph": "p"
    }
     """
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
    
""" 
def shape_CustomURL(num, pages):
  if len(pages[num]["properties"]["CustomURL"]["rich_text"]) == 0:
    return ""
  else:
    p = pages[num]["properties"]["CustomURL"]["rich_text"][0]["plain_text"]
    return re.sub(r'\n|\r|\s', '_', p)
 """

def get_q_page(db):
  t_pages = []
  Page_LIST = db["results"]
  for i in range(len(Page_LIST)):
    #input(Page_LIST[i])
    Status = Page_LIST[i]["properties"]["Status"]["status"]["name"]
    if Status == STATUS_GO:
      ID = Page_LIST[i]["id"]
      Title = Page_LIST[i]["properties"]["Title"]["title"][0]["text"]["content"]
      FullForm = shape_FullForm(i, Page_LIST)
      #CustomURL = shape_CustomURL(i, Page_LIST)
      Prompts = shape_Prompts(i, Page_LIST)

      #if len(Page_LIST[i]["properties"]["Prompts"]["rich_text"]) == 0:
      #  Prompts = ""
      #else:
      #  Prompts = Page_LIST[i]["properties"]["Prompts"]["rich_text"][0]["plain_text"]
      t_pages.append(Page(ID, Title, FullForm, Prompts, Status))
      #t_pages.append(Page(ID, Title, CustomURL, Prompts, Status))

  return t_pages

def get_pages():
  res_db = set_db_requests(DB_ID, Key)
  dict_db = res_db.json()
  #dumps_db = json.dumps(dict_db, indent=2, ensure_ascii=False) #for debug
  Queue_INFO = {"elements":[]}
  PAGES = get_q_page(dict_db)
  for page in PAGES:
    "Enables when running Notion AI, Disable when running ChatGPT"
    #page.get_contents()
    Queue_INFO["elements"].append(page.get_all())

  Queue_INFO["checkpoint"] = 1
  with open(TMP_FILE_PATH, mode='w') as f:
    json.dump(Queue_INFO, f, indent=2, ensure_ascii=False)

  """ 
  dumps_Queue = json.dumps(Queue_INFO, indent=2, ensure_ascii=False)

  "デバッグ時データ可視化用"
  #print(dumps_Queue)
  "==============="

  with open(TMP_FILE_PATH, mode='w') as f:
    f.write(dumps_Queue)
   """

def main():
  get_pages()
  """ 
  #DB_ID, Key = get_auth()
  res_db = set_db_requests(DB_ID, Key)

  dict_db = res_db.json()
  dumps_db = json.dumps(dict_db, indent=2, ensure_ascii=False)
  #print(dumps_db)
  #input("wait")
  #print(dict_db)
  #print(dumps_db)
  #CHILD_TREE = {}
  Queue_INFO = {"elements":[]}
  #PAGES = []
  PAGES = get_q_page(dict_db)

  
  #WP_articles = dict_db["results"]
  
  for page in PAGES:
    
    #print("##### BEFORE #####")
    #print(page.get_all())
    #contents = page.get_contents()
    page.get_contents()
    #print(contents)
    #dict_contents = contents.json()
    #dumps_contents = json.dumps(dict_contents, indent=2, ensure_ascii=False)
    #print("##### AFTER #####")
    #print(page.get_all())
    Queue_INFO["elements"].append(page.get_all())

  #print("===== Queue_INFO =====")
  #print(Queue_INFO)
  #dumps_Queue = json.dumps(dict_Queue, indent=2, ensure_ascii=False)

  "デバッグ時データ可視化用"
  dumps_Queue = json.dumps(Queue_INFO, indent=2, ensure_ascii=False)
  #print(dumps_Queue)
  "==============="

  with open(TMP_FILE_PATH, mode='w') as f:
    f.write(dumps_Queue) """

"=================================================="

if __name__ == "__main__":
  main()



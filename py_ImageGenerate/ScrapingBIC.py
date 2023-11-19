import asyncio
from time import time, sleep
import httpx
import os
import shutil
from argparse import ArgumentParser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import subprocess
from time import sleep
import datetime
import re
from concurrent.futures import ThreadPoolExecutor
import json
import itertools
import glob
import sys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib
from googletrans import Translator

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
META_FILE = "metadata.txt"

LOG_DIR = "log"
LOG_FILE = "debug.log"
LOG_FILE_PATH = os.path.join(ROOT_DIR, LOG_DIR, LOG_FILE)

IMAGE_CNT = 5
FILE_EXT = ".jpeg"

def read_config(ele):
  with open(CONFIG_FILE_PATH, mode='r') as f:
    data = json.load(f)
    if ele == "AuthCookie":
      cookie = data["py_ImageGenerate"]["AuthCookie"]
      return cookie
    
    elif ele == "MicrosoftAuth":
      email = data["py_ImageGenerate"]["MicrosoftAuth"]["email"]
      password = data["py_ImageGenerate"]["MicrosoftAuth"]["password"]
      return email, password
    
    elif ele == "PromptCustom":
      c_prompt = data["py_ImageGenerate"]["PromptCustom"]
      return c_prompt
    
    else:
      exit(f"read_config エラー: 引数は 'AuthCookie' / 'MicrosoftAuth' / 'PromptCustom'のいずれかのみ有効 ")

EMAIL, PASSWORD = read_config("MicrosoftAuth")

def set_xpath():
  x_dic = {
    "bing": "//header/div/div/a[@id='id_l']",
    "login": "//div/span/ul/li/a[@id='id_h']",
    "email_box": "//div/input[@type='email']",
    "pass_box": "//div/div/input[@name='passwd']",
    "submit": "//div/div/input[@type='submit']",
    "ID_error": "//div/div/div[@id='usernameError']",
    "pass_error": "//div/div/div[@id='passwordError']",
  }
  return x_dic

def set_target_URL():
  urls = [
    "https://www.bing.com/",
    "https://login.live.com/login.srf",
    "https://login.live.com/ppsecure/post",
    "https://www.bing.com/images/create/"
  ]
  return urls

XPATHs = set_xpath()
URLs = set_target_URL()

def auth_validation(auth_type, elements):
  if len(elements) == 0:
    return
  else:
    exit(f"{auth_type} seems wrong in {CONFIG_FILE} file. Please fix it and try again.")

def validate_cookie(cookie):
  test_prompt = "test"
  test_dir = os.path.join(ROOT_DIR, TMP_DIR, IMAGE_DIR, "0_TEST")
  if os.path.exists(test_dir):
    shutil.rmtree(test_dir)
  os.makedirs(test_dir)

  if cookie == "":
    print(f"AuthCookie is empty in {CONFIG_FILE}!")
    print(f"Getting a valid auth_cookie now and will store in {CONFIG_FILE}...")
    return False
  
  print(f"Found a cache of auth_cookie in {CONFIG_FILE}. Validating if this is valid auth_cookie...")
  test_result = subprocess.run(["python3", "-m", "BingImageCreator", "-U", cookie, "--prompt", test_prompt , "--output-dir", test_dir], capture_output=True)

  if test_result.returncode != 0:
    print("Error executing python3 -m BingImageCreator xxx command.")
    print(f"Getting a valid auth_cookie now and will store in {CONFIG_FILE}...")
    set_config("AuthCookie", string="")
    return False
  
  print("Validate ended up successfully!!!")
  return True


def get_AuthCookie():
  def is_correct_URL(URL, cur_URL):
    if cur_URL.startswith(URL): #ログインページに遷移成功
      print("URL Check PASSED")
      return True
    else:
      print("URL Check FAILED")
      print(URL)
      print(cur_URL)
      return False
    
  def set_xpath():
    x_dic = {
      "bing": "//header/div/div/a[@id='id_l']",
      "login": "//div/span/ul/li/a[@id='id_h']",
      "email_box": "//div/input[@type='email']",
      "pass_box": "//div/div/input[@name='passwd']",
      "submit": "//div/div/input[@type='submit']",
      "ID_error": "//div/div/div[@id='usernameError']",
      "pass_error": "//div/div/div[@id='passwordError']",
    }
    return x_dic
  
  def set_target_URL():
    urls = [
      "https://bing.com/",
      "https://login.live.com/login.srf",
      "https://login.live.com/ppsecure/post",
      "https://www.bing.com/"
    ]
    return urls
    
  login_id, login_pass = read_config("MicrosoftAuth")
  sleep_timer = 1
  XPATHs = set_xpath()
  URLs = set_target_URL()

  "Chrome の起動"
  BROWSER = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install())) # For Mac, Browser version auto-upgrade
  #BROWSER = webdriver.Chrome() # For Mac
  BROWSER.implicitly_wait(2)

  "Bing ホームページに遷移"
  BROWSER.get(URLs[0])
  sleep(sleep_timer)

  cur_url = BROWSER.current_url
  result = BROWSER.find_element(by=By.XPATH, value=XPATHs["bing"])

  "[期待値] Microsoft ログイン画面に遷移"
  result.click()
  sleep(sleep_timer)

  cache_url, cur_url = cur_url, BROWSER.current_url
  check_URL = URLs[1]
  
  if is_correct_URL(check_URL, cur_url) == False:
    print("ログイン画面遷移失敗")
    return False

  "[期待値] ログイン画面でメールアドレスを入力"
  email_box = BROWSER.find_element(by=By.XPATH, value=XPATHs["email_box"])
  submit_button = BROWSER.find_element(by=By.XPATH, value=XPATHs["submit"])
  email_box.send_keys(login_id)

  submit_button.click() # email_submit / エラー頻発
  sleep(sleep_timer)

  auth_validation("ID", BROWSER.find_elements(By.XPATH, value=XPATHs["ID_error"]))
  
  "[期待値] ログイン画面でパスワードを入力"
  pass_box = BROWSER.find_element(by=By.XPATH, value=XPATHs["pass_box"])
  submit_button = BROWSER.find_element(by=By.XPATH, value=XPATHs["submit"])
  pass_box.send_keys(login_pass)

  "[期待値] ログイン後のサインイン維持確認画面に遷移"
  submit_button.click() # pass_submit / エラー頻発
  sleep(sleep_timer)

  auth_validation("Password", BROWSER.find_elements(By.XPATH, value=XPATHs["pass_error"]))
  
  cache_url, cur_url = cur_url, BROWSER.current_url
  check_URL = URLs[2]
  if is_correct_URL(check_URL, cur_url) == False:
    print("サインイン維持確認画面遷移失敗")
    return False

  "[期待値] Bing ホームページに戻る"
  submit_button = BROWSER.find_element(by=By.XPATH, value=XPATHs["submit"])
  submit_button.click()
  sleep(sleep_timer)

  cache_url, cur_url = cur_url, BROWSER.current_url
  check_URL = URLs[3]
  if is_correct_URL(check_URL, cur_url) == False: 
    print("Bingホームページ遷移失敗")
    return False

  "Bing Image Creator で使用する認証クッキーを取得"
  auth_cookie = BROWSER.get_cookie("_U")["value"]
  BROWSER.close()

  set_config("AuthCookie", auth_cookie)
  print("Successfully extracteed auth_cookie")
  return True

def tpe_get_image(dict_prompt: dict, cookie: str):
  title, prompt = list(zip(dict_prompt.keys(), dict_prompt.values()))[0]
  print(title, prompt)
  target_dir = title
  target_dir_path = os.path.join(ROOT_DIR, TMP_DIR, IMAGE_DIR, target_dir)
  meta_file_path = os.path.join(target_dir_path, META_FILE)

  os.makedirs(target_dir_path, exist_ok=True)
  retry_cnt = 5
  start_num = get_image_total(target_dir_path)
  for _ in range(1, retry_cnt+1):
    assign_num = get_image_total(target_dir_path)
    now = datetime.datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
    result = subprocess.run(["python3", "-m", "BingImageCreator", "-U", cookie, "--prompt", prompt, "--output-dir", target_dir_path], capture_output=True)
    if result.returncode == 0:
      increased = get_image_total(target_dir_path) 
      with open(meta_file_path, mode = 'a+') as f:
        f.write(f"File No.: {assign_num}~{increased}, prompt: {prompt}, created_at: {now}\n")
      if increased - start_num >= IMAGE_CNT:
        write_NotionObj(title, increased)
        print(f"Image for {title} generated more than {IMAGE_CNT} successfully")
        return
      
    else:
      print(result)
      input("stop_else")
      set_config("AuthCookie", string="")
      with open(LOG_FILE_PATH, mode='a') as f:
        f.write(result.stderr)
      with open(meta_file_path, mode='a') as f:
        f.write("-----> Error occurred")

      print("--------------------------------------------------")
      print("Error executing python3 -m BingImageCreator xxx command.")
      print(f"Deleting 'AuthCookie' in {CONFIG_FILE} as its cookie for Microsoft Authentication seems wrong.")
      print("Please try running this script again, or report to the developer if the issue keeps occuring.")
      print("--------------------------------------------------")
      exit()
  return

def get_image_total(dir_path):
  ans = len(os.listdir(dir_path)) - 1
  for f in os.listdir(dir_path):
    if not f.endswith(".jpeg") or f.endswith(".jpg") or f.endswith(".png"):
      ans -= 1
  return ans

def get_Bing_auth():
  retry_cnt = 3
  for _ in range(retry_cnt):
    success = get_AuthCookie()
    if success:
      cookie = read_config("AuthCookie")
      return cookie
  else:
    exit(f"Getting auth_cookie failed for {retry_cnt} times.\nCheck auth.txt file for any mistake.")

def set_config(element, string):
  with open(CONFIG_FILE_PATH, mode='r') as f:
    data = json.load(f)
    if element == "AuthCookie":
      data["py_ImageGenerate"]["AuthCookie"] = string
    elif element == "email":
      data["py_ImageGenerate"]["MicrosoftAuth"]["email"] = string
    elif element == "password":
      data["py_ImageGenerate"]["MicrosoftAuth"]["password"] = string
    else:
      exit(f"set_config 実行エラー: element パラメータは 'AuthCookie', 'email', 'password' のいずれかのみ有効")
      
  with open(CONFIG_FILE_PATH, mode='w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

def read_NotionObj() -> list:
  prompts = []
  with open(TMP_FILE_PATH, mode='r') as f:
    data = json.load(f)
  for d in data["elements"]:
    if d["Prompts"] == "":
      p = {d["Title"]: d["Title"]}
    else:
      p = {d["Title"]: d["Prompts"]}
    prompts.append(p)
  return prompts

def write_NotionObj(jobs):
  with open(TMP_FILE_PATH, mode='r') as f:
    data = json.load(f)
  for d in data["elements"]:
    if d["Title"] in jobs.keys():
      d["Images"] = []
      for i in range(len(jobs[d["Title"]])):
        d["Images"].append(jobs[d["Title"]][i])

  data["checkpoint"] = 3
  with open(TMP_FILE_PATH, mode='w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

def get_signin_screen(browser, cnt, timer):
  "[期待値] Microsoft ログイン画面に遷移"
  for i in range(cnt):
    try: #失敗しそうな処理
      sign_in_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.id_button")))
      sign_in_button.click()
      WebDriverWait(browser, timer).until(EC.url_matches(URLs[1]))
    except Exception as e: #失敗時の処理(不要ならpass)
      print(f"failed {sys._getframe().f_code.co_name}, attempt: {i}")
      error = e
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return True
  else: #リトライが全部失敗したときの処理
    print(error)
    return False

def pass_email(browser, cnt, timer):
  "[期待値] email を入力して「次へ」ボタンを押す"
  for i in range(cnt):
    try: #失敗しそうな処理
      email_box = WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
      email_box.send_keys(EMAIL)
      next_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
      next_button.click()
      WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
    except Exception as e: #失敗時の処理(不要ならpass)
      print(f"failed {sys._getframe().f_code.co_name}, attempt: {i}")
      error = e
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return True
  else: #リトライが全部失敗したときの処理
    print(error)
    return False

def pass_password(browser, cnt, timer):
  "[期待値] password を入力して「サインイン」ボタンを押す"
  for i in range(cnt):
    try: #失敗しそうな処理
      sleep(timer)
      pass_box = WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
      pass_box.send_keys(PASSWORD)
      submit_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
      submit_button.click()
      WebDriverWait(browser, timer).until(EC.url_matches(URLs[2]))
    except Exception as e: #失敗時の処理(不要ならpass)
      print(f"failed {sys._getframe().f_code.co_name}, attempt: {i}")
      error = e
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return True
  else: #リトライが全部失敗したときの処理
    print(error)
    return False
    #exit("failed")

def pass_DontShow(browser, cnt, timer):
  "[期待値] 継続サインイン入力画面から bing ホームページへ遷移"
  for i in range(cnt):
    try: #失敗しそうな処理
      DontShow_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
      DontShow_button.click()
      WebDriverWait(browser, timer).until(EC.url_matches(URLs[0]))
    except Exception as e: #失敗時の処理(不要ならpass)
      print(f"failed {sys._getframe().f_code.co_name}, attempt: {i}")
      error = e
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return True
  else: #リトライが全部失敗したときの処理
    print(error)
    return False

def pass_prompts(browser, cnt, short_timer, large_timer, prompt):
  "[期待値] 継続サインイン入力画面から bing ホームページへ遷移"
  for i in range(cnt):
    try: #失敗しそうな処理
      browser.get(URLs[3])
      prompts_box = WebDriverWait(browser, short_timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id='sb_form_q']")))
      prompts_box.send_keys(prompt)
      create_button = WebDriverWait(browser, short_timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[id='create_btn_c']")))
      create_button.click()
      WebDriverWait(browser, large_timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#mmComponent_images_as_1 > ul")))
    except Exception as e: #失敗時の処理(不要ならpass)
      print(f"failed {sys._getframe().f_code.co_name}, attempt: {i}")
      error = e
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def pass_img_urls(browser, cnt, timer) -> list:
  "[期待値] 継続サインイン入力画面から bing ホームページへ遷移"
  for i in range(cnt):
    try: #失敗しそうな処理
      img_url_list = []
      l_row = len(browser.find_elements(By.CSS_SELECTOR, "div#mmComponent_images_as_1 > ul"))
      if l_row > 1:
        for row in range(1, l_row+1):
          l_column = len(browser.find_elements(By.CSS_SELECTOR, f"div#mmComponent_images_as_1 > ul:nth-child({row}) > li"))
          if l_column > 1:
            for column in range(1, l_column+1):
              image = WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, f"div#mmComponent_images_as_1 > ul:nth-child({row}) > li:nth-child({column}) > div > div > a > div > img")))
              img_url = image.get_attribute("src")
              "より高画質の画像をダウンロードする際は有効にする"
              img_url = re.sub(r"\?w=.*pid=ImgGn", "?pid=ImgGn", img_url)
              img_url_list.append(img_url)
          else:
            image = WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, f"div#mmComponent_images_as_1 > ul:nth-child({row}) > li > div > div > a > div > img")))
            img_url = image.get_attribute("src")
            "より高画質の画像をダウンロードする際は有効にする"
            img_url = re.sub(r"\?w=.*pid=ImgGn", "?pid=ImgGn", img_url)
            img_url_list.append(img_url)
      else:
        l_column = len(browser.find_elements(By.CSS_SELECTOR, "div#mmComponent_images_as_1 > ul > li"))
        if l_column > 1:
          for column in range(1, l_column+1):
            image = WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, f"div#mmComponent_images_as_1 > ul > li:nth-child({column}) > div > div > a > div > img")))
            img_url = image.get_attribute("src")
            "より高画質の画像をダウンロードする際は有効にする"
            img_url = re.sub(r"\?w=.*pid=ImgGn", "?pid=ImgGn", img_url)
            img_url_list.append(img_url)
        else:
          image = WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, f"div#mmComponent_images_as_1 > ul > li > div > div > a > div > img")))
          img_url = image.get_attribute("src")
          "より高画質の画像をダウンロードする際は有効にする"
          img_url = re.sub(r"\?w=.*pid=ImgGn", "?pid=ImgGn", img_url)
          img_url_list.append(img_url)
    except Exception as e: #失敗時の処理(不要ならpass)
      print(f"failed {sys._getframe().f_code.co_name}, attempt: {i}")
      error = e
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return img_url_list
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def set_img_dir(title):
  target_dir_path = os.path.join(ROOT_DIR, TMP_DIR, IMAGE_DIR, title)
  os.makedirs(target_dir_path, exist_ok=True)
  return target_dir_path

def download_images(browser, cnt, timer, urls, title, prompt, dir_path) -> list:
  content_type = '.jpeg'
  images = []
  trans_title = jp_en_translate(title)
  now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
  for i, img in zip(range(len(urls)), urls):
    with urllib.request.urlopen(img) as rf:
      img_data = rf.read()
    filename = f"{dir_path}/{trans_title}_{now}_{i}{content_type}"
    with open(filename, mode="wb")as wf:
      wf.write(img_data)
      images.append(os.path.basename(filename))
  print(f"success {sys._getframe().f_code.co_name}")
  return images

def scraping_images(d_prompts) -> dict:
  short_timer = 3
  large_timer = 30
  retry_cnt = 3
  jobs = {}
  fixed_prompt = read_config('PromptCustom')
  print(f"fixed_prompt: {fixed_prompt}")

  "Chrome の起動"
  options = webdriver.ChromeOptions()
  service = ChromeService(executable_path="/Users/satoshi/.wdm/drivers/chromedriver/mac64/116.0.5845.110/chromedriver-mac-arm64/chromedriver")
  with webdriver.Chrome(service=service, options=options) as BROWSER: # For Mac, Browser version auto-upgrade
    BROWSER.implicitly_wait(large_timer)

    auth_check = False
    for i in range(retry_cnt):
      try:
        "Bing ホームページに遷移"
        BROWSER.get(URLs[0])

        if not get_signin_screen(browser=BROWSER, cnt=retry_cnt, timer=short_timer)\
        or not pass_email(browser=BROWSER, cnt=retry_cnt, timer=short_timer)\
        or not pass_password(browser=BROWSER, cnt=retry_cnt, timer=short_timer)\
        or not pass_DontShow(browser=BROWSER, cnt=retry_cnt, timer=short_timer):
          continue

      except Exception as e:
        print(e)
        print("retrying...")
      else: #失敗しなかった場合は、ループを抜ける
        auth_check = True
        print(f"success all login sequence!!! retry count {i}")
        break
    
    if not auth_check:
      exit(f"Authentication sequence failed. Please try again or check {CONFIG_FILE}.")

    for p in d_prompts:
      title, prompt = list(p.items())[0]
      prompt = f"{prompt} {fixed_prompt}"
      print(f"Prompt: {prompt}")
      pass_prompts(browser=BROWSER, cnt=retry_cnt, short_timer=short_timer, large_timer=large_timer, prompt=prompt)
      sleep(short_timer)
      url_list = pass_img_urls(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
      img_dir_path = set_img_dir(title)
      images_list = download_images(browser=BROWSER, cnt=retry_cnt, timer=short_timer, urls=url_list, title=title, prompt=prompt, dir_path=img_dir_path)
      jobs[title] = images_list

  return jobs

def jp_en_translate(string):
  translator = Translator()
  if not (string.isalnum() and string.isascii()):
    string = translator.translate(string, dest='en').text
  return string

def add_custom_prompt(notion_p, fixed_p):
  for i in range(len(notion_p)):
    for title, value in notion_p[i].items():
      notion_p[title] = value + fixed_p
  return notion_p

def get_images():
  "Notion リストから作成した JSON ファイルから Title, Prompts 項目を読み取り"
  prompts_dict = read_NotionObj()
  print(prompts_dict)
  jobs = scraping_images(prompts_dict)
  write_NotionObj(jobs)

def main():
  get_images()

if __name__ == "__main__":
  main()

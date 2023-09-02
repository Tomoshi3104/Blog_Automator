import asyncio
from time import time, sleep
import httpx

import os
import shutil
from argparse import ArgumentParser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
#from webdriver_manager.core.utils import read_version_from_cmd, PATTERN

import urllib
from googletrans import Translator
import pyperclip

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

IMAGE_CNT = 5
FILE_EXT = ".jpeg"

Notify_Human_Check_Sound = "Human verification occurring! Please solve the problem and press enter"


def read_config(ele):
  with open(CONFIG_FILE_PATH, mode='r') as f:
    data = json.load(f)
  if ele in data[os.path.basename(ABS_FILE_DIR)].keys():
    return data[os.path.basename(ABS_FILE_DIR)][ele]
  else:
    print(f"read_config エラー: 有効な引数は下記を参照してください。\n{data.keys()}")
    return
    
SignInOption = read_config("SignInOption")
Valid_SignIn_Options = ["email"]
#Valid_SignIn_Options = ["email", "Google", "Facebook", "Apple"]
USER = read_config("User")
PASSWORD = read_config("password")
SKIP_LOGIN = read_config("SkipAutoLogIn")
IS_NEW_BROWSER = read_config("IsNewBrowser")
IS_NON_STOP = read_config("NonStop")
#ORDER = "\n".join(read_config("Order"))
ORDER_LIST = read_config("Order")

def set_target_URL():
  urls = [
    "https://chat.openai.com/auth/login",
    "https://auth0.openai.com/u/login/identifier",
    "https://auth0.openai.com/u/login/password",
    "https://chat.openai.com",
    "https://chat.openai.com/c"
  ]
  return urls

URLs = set_target_URL()
#print(SignInOption, USER, PASSWORD, ORDER, sep='\n')

""" 
ORDER = "次についてブログ記事を執筆：「VR」について、見出しは合計5段落で全て日本語、第一段落は「VR とは」、最終段落は「まとめ」とすること。"

「MR」 についてブログ記事を書いて
(MR = Mixed Reality)
6段落構成で、各段落は順番に下記で構成されていること
段落1: 「MR とは」
段落2: 「MR の特徴」
段落3: 「MR の動作原理」
段落4: 「MR の応用分野」
段落5: 「未来への展望」
段落6: 「まとめ」
全体はです・ます調で統一して
 """

def read_NotionObj() -> list:
  info = []
  with open(TMP_FILE_PATH, mode='r') as f:
    data = json.load(f)
  for d in data["elements"]:
    if d["FullForm"] == "":
      p = {d["Title"]: d["Title"]}
    else:
      p = {d["Title"]: d["FullForm"]}
    info.append(p)
  return info

"def write_NotionObj(notion_obj, l_sentences):"
def write_NotionObj(l_sentences):
  #print(l_sentences)
  with open(TMP_FILE_PATH, mode='r') as f:
    data = json.load(f)

  for d_sentence in l_sentences:
    title, sentence = list(d_sentence.items())[0]
    #print(title, sentence, sep='\n')
    for i in range(len(data["elements"])):
      if title == data["elements"][i]["Title"]:
        data["elements"][i]["Contents"] = sentence

  data["checkpoint"] = 2
  with open(TMP_FILE_PATH, mode='w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
  return

  print("write_NotionObj")
  with open(TMP_FILE_PATH, mode='r') as f:
    data = json.load(f)
  for d in data["elements"]:
    if d["Title"] == d_sentences:
      d["Images"] = []
      for i in range(max_num, max_num - IMAGE_CNT, -1):
        d["Images"].append(f'{i}{FILE_EXT}')
  with open(TMP_FILE_PATH, mode='w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    #data = json.load(f)

def set_order(d_fullform) -> list:
  f_orders = []
  for f in d_fullform:
    title, fullform = list(f.items())[0]
    orders = []
    for order in ORDER_LIST:
      order = re.sub('{Title}', title, order)
      order = re.sub('{Full Form}', fullform, order)
      orders.append(order)
    d_order = {title: orders}
    f_orders.append(d_order)
  return f_orders

def get_login_screen(browser, cnt, timer):
  "[期待値] ChatGPT ログイン画面に遷移"
  for i in range(cnt):
    try: #失敗しそうな処理
      log_in_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div > button:nth-child(1)")))
      log_in_button.click()
      WebDriverWait(browser, timer).until(EC.url_matches(URLs[1]))
    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def pass_user(browser, cnt, timer):
  "[期待値] email を入力して「次へ」ボタンを押す"
  for i in range(cnt):
    try: #失敗しそうな処理
      user_box = WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id='username']")))
      user_box.send_keys(USER)
      next_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='button-login-id']")))
      #next_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
      next_button.click()
      #WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id='password']")))
      WebDriverWait(browser, timer).until(EC.url_matches(URLs[2]))
    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def pass_password(browser, cnt, timer):
  "[期待値] password を入力して「サインイン」ボタンを押す"
  for i in range(cnt):
    try: #失敗しそうな処理
      pass_box = WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
      pass_box.send_keys(PASSWORD)
      submit_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='button-login-password']")))
      #submit_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
      submit_button.click()
      WebDriverWait(browser, timer).until(EC.url_matches(URLs[3]))
    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def pass_popup(browser, cnt, timer):
  "[期待値] 継続サインイン入力画面から bing ホームページへ遷移"
  for i in range(cnt):
    try: #失敗しそうな処理
      #if browser.find_element(by=By.CSS_SELECTOR, value="div[id='radix-:ri:']"):
      #print("here")
      #close_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#radix-\:rf\: > div.p-4.sm\:p-6.sm\:pt-4 > div > div.flex.flex-row.justify-end > button")))
      #close_button.click()
      #if browser.find_element(by=By.CSS_SELECTOR, value="#radix-\:rf\:"):
      if WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#radix-\:rf\: > div.p-4.sm\:p-6.sm\:pt-4 > div > div.flex.flex-row.justify-end > button"))):
        #print("yes")
        #radix-\:rf\:
        #close_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#radix-\:ri\: > div.p-4.sm\:p-6.sm\:pt-4 > div > div.flex.flex-row.justify-end > button")))
        close_button = browser.find_element(by=By.CSS_SELECTOR, value="#radix-\:rf\: > div.p-4.sm\:p-6.sm\:pt-4 > div > div.flex.flex-row.justify-end > button")
        #print(close_button)
        #close_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div > div > div > div > div > div > div > button[as='button']")))
        close_button.click()
      WebDriverWait(browser, timer).until(EC.url_matches(URLs[3]))
    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def pass_orders(browser, cnt, short_timer, large_timer, orders):
  for i in range(cnt):
    try: #失敗しそうな処理
      print("pass_orders")
      #input("stop")
      #input("\n".join(orders))
      orders_box = WebDriverWait(browser, short_timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[id='prompt-textarea']")))
      "下記 for loop が失敗する場合の処理"
      #orders_box.send_keys(" ".join(orders))
      "for loop が失敗する場合は上の処理に変更する"
      for order in orders:
        orders_box.send_keys(order)
        orders_box.send_keys(Keys.SHIFT + Keys.ENTER)

      #sleep(short_timer)
      submit_button = WebDriverWait(browser, short_timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.rounded-xl.shadow-xs.dark\:shadow-xs > button")))
      submit_button.click()

      sleep(short_timer)
      aria_hidden_cnt = len(WebDriverWait(browser, short_timer).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[aria-hidden='true']"))))
      print(f"aria-hidden=true: {aria_hidden_cnt}")
      if aria_hidden_cnt > 2:
        sleep(short_timer)
        print("Human Error Check Occurring!")
        for i in range(cnt):
          subprocess.run(["say", "-v", "Daniel", Notify_Human_Check_Sound])
          sleep(short_timer)
        while aria_hidden_cnt > 2:
          input("Please finish the Human Verification and press Enter to move on!")
          aria_hidden_cnt = len(WebDriverWait(browser, short_timer).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[aria-hidden='true']"))))
      
      
      #if WebDriverWait(browser, short_timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "main > div > div.flex-1.overflow-hidden > div > div > div > button.cursor-pointer"))):
        #down_scroll_button = browser.find_elements(by=By.CSS_SELECTOR, value="main > div > div.flex-1.overflow-hidden > div > div > div > button.cursor-pointer")
        #down_scroll_button = WebDriverWait(browser, short_timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "main > div > div.flex-1.overflow-hidden > div > div > div > button.cursor-pointer")))
        #down_scroll_button.click()
      
      sleep(short_timer)
      #__next > div.overflow-hidden.w-full.h-full.relative.flex.z-0 > div.relative.flex.h-full.max-w-full.flex-1.overflow-hidden > div > main > div > div.flex-1.overflow-hidden > div > div > div > button

      """ 
      "スクロールを挟む方法1"
      browser.find_element(By.CSS_SELECTOR, 'body').click()
      browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
      browser.execute_script("window.scrollBy(0, document.body.scrollHeight);")
      "スクロールを挟む方法2"
      actions = ActionChains(browser)
      browser.find_element(By.CSS_SELECTOR, "body").click()
      actions.key_down(Keys.COMMAND).send_keys(Keys.END).key_up(Keys.COMMAND).perform()
       """
      """ 
      #スクロール挟むための試験
      browser.execute_script("window.scrollBy(0, document.body.scrollHeight);")
      actions = ActionChains(browser)
      print(browser.find_element(By.CSS_SELECTOR, "div.relative.flex.h-full.max-w-full.flex-1.overflow-hidden > div > main > div > div.flex-1.overflow-hidden > div > div > div > div:nth-child(2)").text)
      browser.find_element(By.CSS_SELECTOR, "div.relative.flex.h-full.max-w-full.flex-1.overflow-hidden > div > main > div > div.flex-1.overflow-hidden > div > div > div > div:nth-child(2)").click()
      actions.key_down(Keys.COMMAND).send_keys(Keys.ARROW_DOWN).key_up(Keys.COMMAND).perform()
      print("ok")
       """
      #sleep(large_timer)
      #input("test")
      #print(bool(WebDriverWait(browser, large_timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#game-core-frame")))))
      #print(WebDriverWait(browser, large_timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#game-core-frame"))))
      #if browser.find_element(by=By.CSS_SELECTOR, value="#root > div > div.sc-99cwso-0.sc-11w6f91-0.fcBZbp.eWRcSj.home.box.screen > button"):
      """ 
      if browser.find_element(by=By.CSS_SELECTOR, value="iframe[id='game-core-frame']"):
        input("Stuck at Human Check! Please see the screen")
        print(browser.find_element(by=By.CSS_SELECTOR, value="iframe[id='game-core-frame']"))
        close_button = WebDriverWait(browser, large_timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#app > button[aria-label='Close']")))
        close_button.click()
       """
      #if WebDriverWait(browser, large_timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#game-core-frame"))):
      #if WebDriverWait(browser, large_timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#root > div > div.sc-99cwso-0.sc-11w6f91-0.fcBZbp.eWRcSj.home.box.screen > button"))):
      #if WebDriverWait(browser, large_timer).until(EC.url_changes()):
      
    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def end_check(browser, cnt, short_timer, large_timer):
  for i in range(cnt):
    try: #失敗しそうな処理
      print(sys._getframe().f_code.co_name)
      #input()
      #if WebDriverWait(browser, large_timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.flex.items-center.md\:items-end > div > button > div"))).text == "Regenerate":
      #gen_message = WebDriverWait(browser, timer).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div/div/div[1]/div[2]/div/main/div/div[2]/form/div/div[1]/div/div[2]/div/button/div"))).text
      gen_message = WebDriverWait(browser, large_timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.flex.items-center.md\:items-end > div > button > div"))).text
      #print(WebDriverWait(browser, timer).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div/div/div[1]/div[2]/div/main/div/div[2]/form/div/div[1]/div/div[2]/div/button/div"))).text)
      #print(WebDriverWait(browser, timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.flex.items-center.md\:items-end > div > button > div"))).text)
      #input("stop")
      
      while gen_message in ["Stop generating", "Continue generating"]:
        if gen_message == "Continue generating":
          #input("continue_button stop")
          print("continue_button pressed")
          continue_button = WebDriverWait(browser, large_timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.flex.items-center.md\:items-end > div > button")))
          continue_button.click()
          aria_hidden_cnt = len(WebDriverWait(browser, short_timer).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[aria-hidden='true']"))))
          print(f"aria-hidden=true: {aria_hidden_cnt}")
          if aria_hidden_cnt > 2:
            sleep(short_timer)
            print("Human Error Check Occurring!")
            for i in range(cnt):
              subprocess.run(["say", "-v", "Daniel", Notify_Human_Check_Sound])
              sleep(short_timer)
            while aria_hidden_cnt > 2:
              input("Please finish the Human Verification and press Enter to move on!")
              aria_hidden_cnt = len(WebDriverWait(browser, short_timer).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[aria-hidden='true']"))))
        sleep(short_timer)
        gen_message = WebDriverWait(browser, large_timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.flex.items-center.md\:items-end > div > button > div"))).text
      
      "スクロール"
      """ 
      down_scroll_button_cnt = len(browser.find_elements(by=By.CSS_SELECTOR, value="main > div > div.flex-1.overflow-hidden > div > div > div > button.cursor-pointer"))
      #down_scroll_button_cnt = len(WebDriverWait(browser, short_timer).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "main > div > div.flex-1.overflow-hidden > div > div > div > button.cursor-pointer"))))
      print(down_scroll_button_cnt)
      if down_scroll_button_cnt >= 1:
        print("pushing down scroll button")
        WebDriverWait(browser, short_timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "main > div > div.flex-1.overflow-hidden > div > div > div > button.cursor-pointer"))).click()
       """
      #input()
      #copied_text = browser.execute_script("return window.getSelection().toString();")
      #print(f"copied_text:\n{copied_text}")

    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")


def get_sentences(browser, cnt, timer):
  browser.find_element(By.CSS_SELECTOR, 'body').click()
  browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
      
  for i in range(cnt):
    try: #失敗しそうな処理
      print("get_sentences")
      #input()
      screen = WebDriverWait(browser, timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.flex.flex-grow.flex-col.gap-3 > div > div")))
      screen.click()
      action_chains = ActionChains(browser)
      action_chains.key_down(Keys.COMMAND).key_down(Keys.SHIFT).send_keys("c").key_up(Keys.COMMAND).key_up(Keys.SHIFT).perform()
      #input("ok")
      copied_texts = pyperclip.paste()
      #print(pyperclip.paste())
      sentences = []
      for s in copied_texts.split("\n"):
        sentences.append(s)
      #input()
      #copied_text = browser.execute_script("return window.getSelection().toString();")
      #print(f"copied_text:\n{copied_text}")

    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return sentences
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def scraping_new_browser(l_orders) -> list:
  short_timer = 3
  large_timer = 60
  retry_cnt = 3
  jobs = {}

  "Chrome の起動"
  #subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--remote-debugging-port=9222", "--profile-directory='Profile 12'"])
  #subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--remote-debugging-port=9222", "--user-data-dir=/Users/satoshi/Library/Application Support/Google/Chrome/" "--profile-directory='Profile 12'"])
  #sleep(short_timer)
  service = ChromeService(ChromeDriverManager().install())
  #service = ChromeService(executable_path="/Users/satoshi/.wdm/drivers/chromedriver/mac64/116.0.5845.110/chromedriver-mac-arm64/chromedriver")
  #print(service)
  options = webdriver.ChromeOptions()
  #options.add_argument('--headless')
  #options.add_argument('--start-maximized')
  """ 
  if SKIP_LOGIN:
    print("skipping login")
    options.add_argument("--user-data-dir=/Users/satoshi/Library/Application Support/Google/Chrome/")
    options.add_argument("--profile-directory=Profile 15")
    options.add_argument("--remote-debugging-port=9222")
   """
  #options.debugger_address = "localhost:9222"  # 前のステップで取得したポート番号に置き換える
  #options.add_argument("--headless")
  #options.add_argument("--no-sandbox")
  """
  driver = webdriver.BROWSER(service=service)
  url = driver.command_executor._url       #"http://127.0.0.1:60622/hub"
  session_id = driver.session_id  
  driver = webdriver.Remote(command_executor=url,desired_capabilities={})
  driver.close()   # this prevents the dummy browser
  driver.session_id = session_id
  """
  #options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
  #driver = webdriver.Chrome(executable_path=driver_path, options=options)
  #options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36")
  
  "既存ブラウザを使用しない場合"
  service = ChromeService(ChromeDriverManager().install())
  options = webdriver.ChromeOptions()
  options.add_argument('--start-maximized')
  with webdriver.Chrome(service=service, options=options) as BROWSER: # For Mac, Browser version auto-upgrade
    print(BROWSER.current_url)
  #with webdriver.Chrome(options=options) as BROWSER: # For Mac, Browser version auto-upgrade
    BROWSER.implicitly_wait(large_timer)
    #input("15")
    #sleep(60)

    "ChatGPT ログイン画面に遷移"
    sleep(10)
    BROWSER.get(URLs[0])
    get_login_screen(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    pass_user(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    sleep(short_timer) #URL遷移が発生しない場合はsleepを入れないと、その後の処理がおかしくなる
    pass_password(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    pass_popup(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    #for d in d_orders:
    l_sentences = []
    for d_order in l_orders:
      title, orders = list(d_order.items())[0]
      d_sentences = {}
      pass_orders(browser=BROWSER, cnt=retry_cnt, short_timer=short_timer, large_timer=large_timer, orders=orders)
      end_check(browser=BROWSER, cnt=retry_cnt, short_timer=short_timer, large_timer=large_timer)
      sentences = get_sentences(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
      d_sentences[title] = sentences
      l_sentences.append(d_sentences)
      sleep(short_timer)
  return l_sentences


def scraping_exist_browser(l_orders) -> list:
  #sleep_timer = 2
  short_timer = 3
  large_timer = 60
  retry_cnt = 3
  jobs = {}
  #print(d_orders)

  "Chrome の起動"
  #run_cmd = subprocess.Popen('/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --profile-directory="Profile 15"', shell=True)
  print("For Mac: run the following command in terminal and get pass ChatGPT login. After that, press 'yes' and enter.")
  print('Command: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --profile-directory="Profile 18"')
  print("Tips: profile-directory can be found under '/Users/<username>/Library/Application Support/Google/Chrome/' folder")
  if not IS_NON_STOP:
    while True:
      if input("Are you ready for Scraping? (yes/no): ").lower() in ["y","yes"]:
        break
  #subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--remote-debugging-port=9222", "--profile-directory='Profile 12'"])
  #subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--remote-debugging-port=9222", "--user-data-dir=/Users/satoshi/Library/Application Support/Google/Chrome/" "--profile-directory='Profile 12'"])
  #sleep(short_timer)
  service = ChromeService(ChromeDriverManager().install())
  #service = ChromeService(executable_path="/Users/satoshi/.wdm/drivers/chromedriver/mac64/116.0.5845.110/chromedriver-mac-arm64/chromedriver")
  #print(service)
  options = webdriver.ChromeOptions()
  #options.add_argument('--headless')
  options.add_argument('--start-maximized')
  """ 
  if SKIP_LOGIN:
    print("skipping login")
    options.add_argument("--user-data-dir=/Users/satoshi/Library/Application Support/Google/Chrome/")
    options.add_argument("--profile-directory=Profile 15")
    options.add_argument("--remote-debugging-port=9222")
   """
  #options.debugger_address = "localhost:9222"  # 前のステップで取得したポート番号に置き換える
  #options.add_argument("--headless")
  #options.add_argument("--no-sandbox")
  """
  driver = webdriver.BROWSER(service=service)
  url = driver.command_executor._url       #"http://127.0.0.1:60622/hub"
  session_id = driver.session_id  
  driver = webdriver.Remote(command_executor=url,desired_capabilities={})
  driver.close()   # this prevents the dummy browser
  driver.session_id = session_id
  """
  options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
  #driver = webdriver.Chrome(executable_path=driver_path, options=options)
  #options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36")
  BROWSER = webdriver.Chrome(service=service, options=options)# For Mac, Browser version auto-upgrade
  BROWSER.implicitly_wait(short_timer)

  for i in range(len(BROWSER.window_handles)):
    BROWSER.switch_to.window(BROWSER.window_handles[i])
    #time.sleep(10)
    if BROWSER.current_url != "https://chat.openai.com/":
      continue
    else:
      break
  #sleep(10)
  """ 
  if not SKIP_LOGIN:
    BROWSER.get(URLs[0])
    get_login_screen(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    pass_user(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    sleep(short_timer) #URL遷移が発生しない場合はsleepを入れないと、その後の処理がおかしくなる
    pass_password(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
  pass_popup(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    """
  #for d in d_orders:
  l_sentences = []
  for d_order in l_orders:
    title, orders = list(d_order.items())[0]
    d_sentences = {}
    pass_orders(browser=BROWSER, cnt=retry_cnt, short_timer=short_timer, large_timer=large_timer, orders=orders)
    end_check(browser=BROWSER, cnt=retry_cnt, short_timer=short_timer, large_timer=large_timer)
    sentences = get_sentences(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    d_sentences[title] = sentences
    l_sentences.append(d_sentences)
    sleep(short_timer)

  """ else:
    print(f"current_url error: {BROWSER.current_url}")
    exit() """
  BROWSER.quit()
  return l_sentences

      #url_list = pass_img_urls(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
      #img_dir_path = set_img_dir(title)
      #images_list = download_images(browser=BROWSER, cnt=retry_cnt, timer=short_timer, urls=url_list, prompt=orders, dir_path=img_dir_path)
      #jobs[title] = images_list
  #return jobs

def get_blog_contents():
  if SignInOption not in Valid_SignIn_Options:
    print(f"現在対応中の SignInOption は下記の通りです。config ファイルで有効な設定に変更してください。\n{Valid_SignIn_Options}")
    exit()
  FullForm_dict = read_NotionObj()
  print(FullForm_dict)
  formed_orders = set_order(FullForm_dict)

  if IS_NEW_BROWSER:
    "ブラウザを新しく開く場合(cloudflare 対策無し)"
    sentences_list = scraping_new_browser(formed_orders)
  else:
    "既存ブラウザを用いる場合(cloudflare 対策有り)"
    sentences_list = scraping_exist_browser(formed_orders)

  #write_NotionObj(FullForm_dict, sentences_list)
  write_NotionObj(sentences_list)
  return

def main():
  get_blog_contents()
  return

if __name__ == "__main__":
  main()
  
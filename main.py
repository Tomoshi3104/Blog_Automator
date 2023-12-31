""" 
WARNING:
Different version may result in unexpected behavior.
==========
Python             3.11.1
BingImageCreator   0.4.4
PyYAML             6.0.1
selenium           4.10.0
requests           2.31.0

2023/08/01
 """

import os
import json
from argparse import ArgumentParser
from py_Notion import ReadDB
from py_ChatGPT import ScrapingCGPT
from py_ImageGenerate import ScrapingBIC
from py_WordPress import PostArticle, UploadImage

ABS_FILE_DIR = os.path.dirname(__file__)
ABS_FILE_PATH = os.path.abspath(__file__)
ROOT_DIR = os.path.dirname(__file__)

TMP_DIR = "tmp"
TMP_FILE = "Notion_Pages.json"
TMP_FILE_PATH = os.path.join(ROOT_DIR, TMP_DIR, TMP_FILE)

last_endpoint = 4

def get_position():
  argparser = ArgumentParser()
  argparser.add_argument(
    '-e', '--end', 
    type=int, 
    nargs='?', 
    default=last_endpoint, 
    choices=range(last_endpoint+1), 
    help=f'Specify endpoint number from the below list.\n{list(range(last_endpoint+1))}'
    )
  argparser.add_argument(
    '-c', '--current_checkpoint', 
    action="store_true", 
    help=f'only shows current checkpoint {TMP_FILE} contains.'
    )
  return argparser.parse_args()

def find_checkpoint():
  try:
    with open(TMP_FILE_PATH, mode='r') as f:
      data = json.load(f)
  except FileNotFoundError as e:
    print(e)
    return 0
  return data["checkpoint"]

def main():
  args = get_position()
  checkpoint = find_checkpoint()
  if args.current_checkpoint:
    print(f"Current checkpoint: {checkpoint}")
    exit()
  if checkpoint <= 0 and args.end >= 0:
    "Notion AI のタスク名、AI記事を取得。タスク名は prompt.txt に保存"
    ReadDB.get_pages()
    print("Reading Database from Notion: Done")

  if checkpoint <= 1 and args.end >= 1:
    "ChatGPT を利用して自動記事生成"
    ScrapingCGPT.get_blog_contents()
    print("Scraping blog sentences from ChatGPT: Done")

  if checkpoint <= 2 and args.end >= 2:
    "BingImageCreator を利用して自動画像生成"
    ScrapingBIC.get_images()
    print("Scraping images from BingImageCreator: Done")

  if checkpoint <= 3 and args.end >= 3:
    "WordPress に画像を投稿"
    UploadImage.post_images()
    print("Uploading images to WordPress: Done")

  if checkpoint <= 4 and args.end >= 4:
    "WordPress に記事を投稿"
    PostArticle.post_articles()
    print("Posting articles to WordPress: Done")

if __name__ == "__main__":
  main()

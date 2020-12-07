import argparse
import pprint
import datetime
import numpy as np
import pandas as pd
import pprint
import praw
import sys
import time
import traceback 

from params import *
from psaw import PushshiftAPI
from tqdm import tqdm

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)
  sys.stderr.flush()

def has_delta(comment):
  for indicator in VALID_DELTA_INDICATORS:
    if indicator in comment.lower():
      return True
    if indicator in comment:
      return True
  return False

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--filename", required=True)
  args = ap.parse_args()
  
  user_flair_group_filename = args.filename
  folder = "/".join(args.filename.split("/")[:-1])
  timestamp = "-".join(user_flair_group_filename.split("-")[1:])
  user_reddit_stats_filename = folder + "/user_reddit_stats-" + timestamp
  user_cmv_comments_filename = folder + "/user_cmv_comments-" + timestamp
  user_cmv_posts_filename = folder + "/user_cmv_posts-" + timestamp

  # convert EST timestamp to UTC epoch
  epoch_est = datetime.datetime.strptime(timestamp[:-4], "%Y-%m-%d-%H-%M-%S") # this is an EST local epoch
  epoch_utc = epoch_est.astimezone(datetime.timezone.utc)
  epoch_est = int(epoch_est.strftime("%s"))
  epoch_utc = int(epoch_utc.strftime("%s"))

  users = []
  with open(user_reddit_stats_filename, "r") as f:
    for line in f:
      line = line.strip()
      fields = line.split("\t")
      username = fields[0] # does not include users suspended from reddit
      users.append(username)

  api = PushshiftAPI()

  # get all comments
  user_comments = {}
  for user in tqdm(users):
    user_comments[user] = []
    for comment in api.search_comments(subreddit='changemyview',
                                       author=user,
                                       filter=['created_utc', 'id', 'parent_id'],
                                       before=epoch_utc):
      user_comment = [comment.id, comment.parent_id, comment.created_utc]
      user_comments[user].append(user_comment)
  
  # get all posts
  user_posts = {}
  for user in tqdm(users):
    user_posts[user] = []
    for post in api.search_submissions(subreddit='changemyview',
                                       author=user,
                                       filter=['created_utc', 'id'],
                                       before=epoch_utc):
      user_post = [post.id, post.created_utc]
      user_posts[user].append(user_post)

  with open(user_cmv_comments_filename, "w") as f:
    for user, comments in user_comments.items():
      num_comments = len(comments)
      for comment in comments:
        comment_id, comment_parent_id, comment_created_utc = comment
        f.write(user + "\t" + str(num_comments) + "\t" + comment_id + "\t" +
                comment_parent_id + "\t" + str(comment_created_utc) + "\n")
 
  with open(user_cmv_posts_filename, "w") as f:
    for user, posts in user_posts.items():
      num_posts = len(posts)
      for post in posts:
        post_id, post_created_utc = post
        f.write(user + "\t" + str(num_posts) + "\t" + post_id + "\t" +
                str(post_created_utc) + "\n")

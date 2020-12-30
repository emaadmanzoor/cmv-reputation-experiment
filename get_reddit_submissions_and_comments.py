#!/usr/bin/env python

import glob
import json
import sys
import time

from psaw import PushshiftAPI
from datetime import datetime, timezone

DATA_DIR = "data/cmv/"

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

if __name__ == "__main__":
  start_time = time.strftime("%Y-%m-%d-%H-%M-%S")
  submissions_file = DATA_DIR + start_time + "_submissions.jsonlist"
  comments_file = DATA_DIR + start_time + "_comments.jsonlist"

  before_est = datetime.strptime(start_time, "%Y-%m-%d-%H-%M-%S")
  before_utc = before_est.astimezone(timezone.utc)
  before_utc = int(before_utc.strftime("%s"))

  after_utc = 0
  most_recent_timestamp = "1970-01-01-00-00-00"
  existing_files = glob.glob(DATA_DIR + "*submissions.jsonlist")
  if len(existing_files) > 0:
    most_recent_submissions_file = existing_files[-1]
    most_recent_timestamp = most_recent_submissions_file.split("_")[0]
    most_recent_timestamp = most_recent_timestamp.split("/")[-1]

    after_est = datetime.strptime(most_recent_timestamp, "%Y-%m-%d-%H-%M-%S")
    after_utc = after_est.astimezone(timezone.utc)
    after_utc = int(after_utc.strftime("%s"))

  eprint("Getting submissions:",
         most_recent_timestamp, after_utc, "to",
         start_time, before_utc)
  
  api = PushshiftAPI()
  submissions = []
  for submission in api.search_submissions(subreddit='changemyview',
                                           filter=['author', 'created_utc',
                                                   'full_link', 'id',
                                                   'retrieved_on', 'title',
                                                   'selftext'],
                                           after=after_utc,
                                           before=before_utc):
    submissions.append(submission)

    if len(submissions) % 10 == 0:
      eprint(".", end="")
      sys.stderr.flush()
  eprint("done.")

  with open(submissions_file, "w") as f:
    for submission in submissions:
      f.write(json.dumps(submission.d_) + "\n")
  
  eprint("Getting comments:",
         most_recent_timestamp, after_utc, "to",
         start_time, before_utc)

  comments = []
  for comment in api.search_comments(subreddit='changemyview',
                                     filter=['author', 'created_utc',
                                             'author_flair_text',
                                             'permalink', 'id', 'parent_id',
                                             'retrieved_on', 'body',
                                             'link_id'],
                                           after=after_utc,
                                           before=before_utc):
    comments.append(comment)

    if len(comments) % 10 == 0:
      eprint(".", end="")
      sys.stderr.flush()
  eprint("done.")
  
  with open(comments_file, "w") as f:
    for comment in comments:
      f.write(json.dumps(comment.d_) + "\n")

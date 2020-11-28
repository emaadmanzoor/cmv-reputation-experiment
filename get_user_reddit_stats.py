import argparse
import numpy as np
import pprint
import praw
import sys
import time

from params import *
from tqdm import tqdm

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--filename", required=True)
  args = ap.parse_args()
  
  user_flair_group_filename = args.filename
  timestamp = "-".join(user_flair_group_filename.split("-")[1:])
  user_redditstats_filename = "user_reddit_stats-" + timestamp

  # read user/flair/treatment assignment file
  users = []
  deltas = []
  strata = []
  treatments = []
  with open(user_flair_group_filename, "r") as f:
    for line in f:
      user, flair, delta, stratum, css, treatment = line.strip().split("\t")
      users.append(user)
      deltas.append(int(delta))
      strata.append(int(stratum))
      treatments.append(int(treatment))
  deltas = np.array(deltas)
  strata = np.array(strata)
  treatments = np.array(treatments)

  reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                       password=PASSWORD, username=USERNAME,
                       user_agent=USER_AGENT)

  # username, comment karma, link karma, created_utc, verified, mod
  user_reddit_stats = []
  for user in tqdm(users[:5]):
    redditor = reddit.redditor(user)
    user_reddit_stats.append([user, redditor.comment_karma, redditor.link_karma,
                              redditor.created_utc, redditor.has_verified_email,
                              redditor.is_mod, redditor.is_gold])
    time.sleep(0.25)

  # write stratum and treatment status to disk
  with open(user_redditstats_filename, "w") as f:
    for idx in range(len(user_reddit_stats)):
      user, comment_karma, link_karma, created_utc,\
        verified, mod, gold = user_reddit_stats[idx]
      treated = treatments[idx]
      stratum = strata[idx]

      f.write(user + "\t" + str(treated) + "\t" + str(stratum) + "\t" +
              str(comment_karma) + "\t" + str(link_karma) + "\t" +
              str(created_utc) + "\t" + str(verified) + "\t" + str(mod) + "\t" +
              str(gold) + "\n")

  eprint("Reddit API limits:", reddit.auth.limits)

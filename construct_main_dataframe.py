#!/usr/bin/env python

import argparse
import glob
import json
import pandas as pd
import re
import spacy
import sys
import time

from tqdm import tqdm

regex = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""

nlp = spacy.load('en', disable=['parser', 'ner'])

excluded_posts = ["/r/changemyview report:",
                  "You Are Not So Smart", "Podcast",
                  "Fresh Topic Friday",
                  "Meta Monday", "[META]", "[meta]",
                   "Mod Post", "[MOD POST]", "[Mod Cross-Post]", "[Mod-Post]", "[Modpost]",
                  "PSA",
                  "Sexless Saturday",
                  "you are Subreddit of the Day",
                  "Taking Mod Applications"
                  ]
VALID_DELTA_INDICATORS = ["!delta", "Δ", "∆", "&#916;", "&#8710;", "&Delta;",
                          "∆", "∇", "▲", "△"] # from deltabot four

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

def has_delta(comment):
  if (comment["author"] != "DeltaBot"):
    for indicator in VALID_DELTA_INDICATORS:
      if indicator in comment["body"].lower():
        return True
      if indicator in comment["body"]:
        return True
  return False

def clean_text(text):
  return text
  doc = re.sub(regex, '', text, flags=re.MULTILINE) # remove URLs
  sentences = []
  for sentence in doc.split("\n"):
    if len(sentence) == 0:
      continue
    if "*Hello, " in sentence:
      continue
    sentences.append(sentence)
  doc = nlp("\n".join(sentences))
  doc = " ".join([token.lemma_.lower().strip() for token in doc
                  if (not token.is_stop)
                      and (not token.like_url)
                      and (not token.lemma_ == "-PRON-")
                      and (not len(token) < 1)
                      and (not token.is_punct)
                      and (not token.is_space)])
  return doc

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--data-folder", required=True)
  args = ap.parse_args()
  data_folder = args.data_folder

  # load submissions
  submission_files = glob.glob(data_folder + "/*_submissions.jsonlist")
  submission_files = sorted(submission_files)
  
  submission_files_start_timestamp = submission_files[0].split("/")[-1].split("_")[0]
  submission_files_end_timestamp = submission_files[-1].split("/")[-1].split("_")[0]
  submissions_df_filename = data_folder + "/submissions_df_" +\
      submission_files_start_timestamp + "_to_" + submission_files_end_timestamp +\
      ".parquet"
  eprint("Submissions file:", submissions_df_filename)

  rows = []
  for submission_file in submission_files:
    with open(submission_file, "r") as f:
      for line in f:
        d = json.loads(line.strip())

        skip = False  # exclude non-debate posts
        for string in excluded_posts:
          if string.lower() in d["title"].lower():
            skip = True
            break
        if skip:
            continue
        
        if d["author"] == "AutoModerator":  # exclude automoderator comments
            continue
        if not "selftext" in d:
            d["selftext"] = ""

        rows.append([d["author"],
                     d["created_utc"],
                     d["full_link"],
                     d["id"],
                     d["retrieved_on"],
                     d["selftext"],
                     d["title"]])
  
  posts_df = pd.DataFrame(rows)
  posts_df = posts_df.drop_duplicates(keep="last")
  posts_df.columns = ["post_author", "created_utc", "full_link",
                      "post_id", "retrieved_on", "text", "title"]
  posts_df['created_dt'] = pd.to_datetime(posts_df['created_utc'], unit='s')
  assert not posts_df.isnull().values.any()

  eprint("Cleaning submission text...", end="")
  t = time.time()
  posts_df["clean_title"] = posts_df["title"].apply(clean_text)
  posts_df["clean_text"] = posts_df["text"].apply(clean_text)
  eprint("done in", time.time() - t, "s")

  posts_df.set_index("post_id").to_parquet(submissions_df_filename, index=True)
  eprint("Submissions dataframe written.")
  
  # load comments
  comment_files = glob.glob(data_folder + "/*_comments.jsonlist")
  comment_files = sorted(comment_files)
  comment_files.append(data_folder + "/missing_comments.jsonlist")
  
  comment_files_start_timestamp = comment_files[0].split("/")[-1].split("_")[0]
  comment_files_end_timestamp = comment_files[-2].split("/")[-1].split("_")[0]
  comments_df_filename = data_folder + "/comment_df_" +\
      comment_files_start_timestamp + "_to_" + comment_files_end_timestamp +\
      ".parquet"
  eprint("Comments file:", comments_df_filename)

  rows = []
  for comment_file in comment_files:
    with open(comment_file, "r") as f:
      for line in f:
        d = json.loads(line.strip())

        if not "retrieved_on" in d:
          d["retrieved_on"] = -1
        if not "permalink" in d:
          d["permalink"] = ""
        
        rows.append([d["author"],
                     d["author_flair_text"],
                     d["body"],
                     d["created_utc"],
                     d["id"],
                     d["link_id"],
                     d["parent_id"],
                     d["permalink"],
                     has_delta(d)])

  comments_df = pd.DataFrame(rows)
  comments_df = comments_df.drop_duplicates(keep="last")
  comments_df.columns = ["author", "author_flair_text", "text",
                         "created_utc", "id", "post_id", "parent_id",
                         "permalink", "has_delta"]
  comments_df['created_dt'] = pd.to_datetime(comments_df['created_utc'], unit='s')
  comments_df["author_flair_text"] = comments_df["author_flair_text"].fillna("")
  comments_df["post_id"] = comments_df["post_id"].apply(lambda x: x[3:])
  comments_df["parent_id"] = comments_df["parent_id"].apply(lambda x: x[3:])
  comments_df = comments_df[comments_df["post_id"].isin(posts_df["post_id"].values)]
  comments_df = comments_df.set_index("id")
  assert not comments_df.isnull().values.any()

  eprint("Cleaning comment text...", end="")
  t = time.time()
  comments_df["clean_text"] = comments_df["text"].apply(clean_text)
  eprint("done in", time.time() - t, "s")

  # mark comments as successful or not
  eprint("Marking successful comments...")
  t = time.time()
  comment_parent_df = comments_df[["parent_id", "author"]]
  comment_post_df = pd.merge(posts_df.reset_index()[["post_id", "post_author"]],
                             comments_df.reset_index()[["post_id", "id", "parent_id",
                                                        "author", "text", "has_delta"]],
                             suffixes=["_post", "_comment"],
                             how="inner", on="post_id", validate="one_to_many")

  op_delta_responses = comment_post_df[(comment_post_df["has_delta"]==True) &
                                       (comment_post_df["author"]==\
                                       comment_post_df["post_author"])]

  successful_response_ids = set([])
  for row in tqdm(op_delta_responses.itertuples()):
    current_post_id = row.post_id
    comment_id = row.id
    author_post = row.post_author

    current_comment_id = comment_id  # id of op delta post
    current_parent_id, current_comment_author =\
        comment_parent_df.loc[current_comment_id]

    if current_parent_id == current_post_id:
      continue # ignore op deltas to themself

    while current_parent_id != current_post_id: # stop at immediate response
      current_comment_id = current_parent_id # go up one level to response
     
      if not current_comment_id in comment_parent_df.index:
        print(current_comment_id)
        break
    
      current_parent_id, current_comment_author =\
          comment_parent_df.loc[current_comment_id]

      if current_parent_id == current_post_id and\
         current_comment_author != author_post:
           successful_response_ids.add(current_comment_id)

  comments_df["successful"] = None
  comments_df["immediate"] = False
  comments_df.loc[comments_df["parent_id"]==comments_df["post_id"],
                  "immediate"] = True

  comments_df.loc[comments_df.index.isin(successful_response_ids),
                  "successful"] = True
  comments_df.loc[(comments_df["parent_id"]==comments_df["post_id"]) &
                  (~comments_df.index.isin(successful_response_ids)),
                  "successful"] = False

  eprint("Done in", time.time() - t, "s")

  # mark comment authors as treatment or control
  user_group_files = glob.glob("user_flair_group-*")
  user_group_files = sorted(user_group_files)
  user_group_file = user_group_files[-1] # most recent assignments

  user_group_assignments = []
  with open(user_group_file, "r") as f:
    for line in f:
      author, delta_text, delta_num, stratum, flair_class, group =\
          line.strip().split("\t")
      user_group_assignments.append([author, int(stratum), int(group)])
  user_group_assignments = pd.DataFrame(user_group_assignments)
  user_group_assignments.columns = ["author", "stratum", "group"]

  comments_df = pd.merge(comments_df, user_group_assignments,
                         on="author", how="left",
                         validate="many_to_one")
  comments_df["group"] = comments_df["group"].fillna(0)
  comments_df["stratum"] = comments_df["stratum"].fillna(0)

  comments_df.to_parquet(comments_df_filename, index=True)
  eprint("Comments dataframe written.")

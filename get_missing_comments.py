from psaw import PushshiftAPI
import json

missing = []
with open("missing_comment_ids.txt", "r") as f:
  for line in f:
    line = line.strip()
    missing.append(line)
missing = set(missing)
print(len(missing))

api = PushshiftAPI()
missing_comments_json = list(api.search_comments(subreddit='changemyview',
                                     filter=['author', 'created_utc',
                                             'author_flair_text',
                                             'permalink', 'id', 'parent_id',
                                             'retrieved_on', 'body',
                                             'link_id'],
                             ids=set(missing), limit=10000))

with open("data/cmv/missing_comments.jsonlist", "w") as f:
  for comment in missing_comments_json:
    f.write(json.dumps(comment.d_) + "\n")

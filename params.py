#!/usr/bin/env python

CLIENT_ID = "zlrUKliWyT65ng"
CLIENT_SECRET = "GKZ4G2df_YZOZ5V9mF-J-lJDDDo"
USERNAME = "entsnack"
PASSWORD = "claustrophobic"
SUBREDDIT = "ChangeMyView"
FLAIR_HIDING_TEMPLATE_ID = "FLAIR_TEMPLATE_ID"
USER_GROUPS_FILENAME = "user_flair_group"
USER_AGENT = "web:zlrUKliWyT65ng:0.1 (by u/entsnack)"
MAX_STRATUM = 7

VALID_DELTA_INDICATORS = ["!delta", "Δ", "∆", "&#916;", "&#8710;", "&Delta;",
                          "∆", "∇", "▲", "△"] # from deltabot four

def get_stratum(d):
    if d == 0:
        return 0
    elif d >= 1 and d < 10:
        return 1
    elif d >= 10 and d < 20:
        return 2
    elif d >= 20 and d < 30:
        return 3
    elif d >= 30 and d < 40:
        return 4
    elif d >= 40 and d < 50:
        return 5
    elif d >= 50 and d < 100:
        return 6
    elif d >= 100:
        return 7

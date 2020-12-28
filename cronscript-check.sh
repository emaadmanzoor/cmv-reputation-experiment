echo "cronscript check running..." >> run.log
python randomize-flair.py --update 2>>run.log 1>>run.log
python check-flair.py 2>>run.log 1>>run.log

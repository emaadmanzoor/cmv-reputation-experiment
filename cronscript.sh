echo "cronscript running..." >> run.log
#cd /home/emanzoor/dev/cmv-reputation-experiment
#. ./cmvexp/bin/activate
#python --version >> run.log
python randomize-flair.py --update 2>>run.log 1>>run.log
python update-flair.py 2>>run.log 1>>run.log
python check-flair.py 2>>run.log 1>>run.log

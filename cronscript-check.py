import schedule
import subprocess
import time

def check_job():
    start_time = time.strftime("%Y-%m-%d-%H-%M-%S")
    print("Calling cronscript-check.sh at:", start_time)
    rc = subprocess.call("./cronscript-check.sh", shell=True)

schedule.every(60).seconds.do(check_job)

while True:
    schedule.run_pending()
    time.sleep(1)

import schedule
import subprocess
import time

def job():
    start_time = time.strftime("%Y-%m-%d-%H-%M-%S")
    print("Calling cronscript.sh at:", start_time)
    rc = subprocess.call("./cronscript.sh", shell=True)

schedule.every(20).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)

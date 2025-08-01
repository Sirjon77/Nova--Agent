from apscheduler.schedulers.background import BackgroundScheduler
import time

def schedule_nova_loop(callback):
    scheduler = BackgroundScheduler()
    scheduler.add_job(callback, 'interval', hours=6)  # Every 6 hours
    scheduler.start()
    print("🔁 Nova loop scheduler activated.")
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
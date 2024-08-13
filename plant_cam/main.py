import cv2
import time
import datetime
from PIL import Image
from telegram import Bot
from telegram.error import TelegramError
from io import BytesIO
import asyncio
import os

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
INTERVAL_IN_S = 60 * 30 # every 10 minutes


# List to hold the file paths of captured images
captured_images = []

def take_picture():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    ret, frame = cap.read()
    cap.release()

    if ret:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"webcam_capture_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        captured_images.append(filename)
        print(f"Image saved as {filename}")
    else:
        print("Error: Could not capture image.")

def create_gif(images, duration=250):
    frames = [Image.open(img) for img in images]
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    gif_filename = f"webcam_timelapse_{timestamp}.gif"

    # Save the GIF to a BytesIO object for easy sending via Telegram
    gif_io = BytesIO()
    frames[0].save(gif_io, format='GIF', append_images=frames[1:], save_all=True, duration=duration, loop=0)
    gif_io.seek(0)

    print(f"GIF created as {gif_filename}")
    return gif_io

async def send_gif_via_telegram(gif_io):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.send_document(chat_id=CHAT_ID, document=gif_io, filename="webcam_timelapse.gif")
        print("GIF sent via Telegram")
    except TelegramError as e:
        print(f"Failed to send GIF: {e}")

async def main():
    last_day = datetime.date.today()
    last_capture_time = time.time()

    try:
        while True:
            current_time = time.time()
            is_daytime = 22 > datetime.datetime.now().hour > 5
            is_interval_passed = current_time - last_capture_time >= INTERVAL_IN_S

            if is_interval_passed and is_daytime:
                take_picture()
                last_capture_time = current_time

            current_day = datetime.date.today()
            if current_day != last_day:
                # A new day has started, send the GIF and reset the list
                if captured_images:
                    gif_io = create_gif(captured_images)
                    await send_gif_via_telegram(gif_io)

                    # Clear the captured images list
                    captured_images.clear()

                # Update last_day to the current day
                last_day = current_day

            await asyncio.sleep(1)  # Check every second to be responsive to interrupts

    except asyncio.CancelledError:
        print("Task was cancelled, cleaning up...")
        raise  # Re-raise the exception to ensure proper cancellation
    except KeyboardInterrupt:
        print("Program stopped by user.")
    finally:
        print("Program stopped.")
        if captured_images:
            gif_io = create_gif(captured_images)
            await send_gif_via_telegram(gif_io)
        else:
            print("No images captured, no GIF created.")

if __name__ == "__main__":
    try:
      asyncio.run(main())
    except KeyboardInterrupt:
        print("Program interrupted, exiting gracefully.")


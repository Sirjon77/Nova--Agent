
import asyncio
import random

# Task limits
MAX_CONCURRENT_TASKS = 5
RETRY_LIMIT = 3
RETRY_DELAY = 5  # seconds

semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

async def generate_video(prompt, platform):
    await asyncio.sleep(random.uniform(0.5, 1.5))  # simulate generation time
    if random.random() < 0.1:  # simulate 10% failure rate
        raise Exception(f"Video generation failed for {platform}")
    print(f"[DISPATCHER] Generated video for {platform} with prompt: {prompt}")
    return f"{platform}_video.mp4"

async def upload_video(file_path, platform):
    await asyncio.sleep(random.uniform(0.5, 1.5))  # simulate upload time
    if random.random() < 0.1:  # simulate 10% failure rate
        raise Exception(f"Upload failed for {platform}")
    print(f"[DISPATCHER] Uploaded {file_path} to {platform}")

async def retry_task(coro, *args):
    attempt = 0
    while attempt < RETRY_LIMIT:
        try:
            return await coro(*args)
        except Exception as e:
            attempt += 1
            print(f"[RETRY] Attempt {attempt} failed: {e}")
            if attempt < RETRY_LIMIT:
                await asyncio.sleep(RETRY_DELAY)
            else:
                print(f"[FAIL] Task permanently failed: {coro.__name__} for args {args}")

async def process_task(prompt, platforms):
    async def handle_platform(platform):
        async with semaphore:
            video = await retry_task(generate_video, prompt, platform)
            if video:
                await retry_task(upload_video, video, platform)

    await asyncio.gather(*(handle_platform(p) for p in platforms))

# Example usage for testing
# asyncio.run(process_task("Motivational Quote", ["TikTok", "YouTube", "Instagram", "Facebook", "LinkedIn"]))

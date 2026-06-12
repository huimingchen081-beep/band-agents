"""Clean demo recording — Playwright captures ONLY browser viewport, not desktop."""
import time
import os
from playwright.sync_api import sync_playwright

DEMO_PAGE = "file:///D:/band-agents-hackathon/demo_replay.html"
OUTPUT_DIR = "D:/band-agents-hackathon/"
VIEWPORT = {"width": 1280, "height": 720}

def main():
    print("[1/3] Launching Chromium...", flush=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--no-sandbox",
            ]
        )
        
        context = browser.new_context(
            viewport=VIEWPORT,
            record_video_dir=OUTPUT_DIR,
            record_video_size=VIEWPORT,
            device_scale_factor=1,
        )
        
        page = context.new_page()
        
        print("[2/3] Loading demo page...", flush=True)
        page.goto(DEMO_PAGE, wait_until="networkidle")
        
        # Let demo run for one full cycle (22s) + buffer
        print("[3/3] Recording demo... (24s)", flush=True)
        time.sleep(24)
        
        # Close gracefully - this saves the video
        context.close()
        browser.close()
    
    # Playwright saves as .webm — find and rename
    time.sleep(2)  # Wait for file write
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.webm') and 'playwright' not in f.lower():
            # This is likely our video
            src = os.path.join(OUTPUT_DIR, f)
            break
    else:
        print("ERROR: No .webm video found!", flush=True)
        return
    
    dst = os.path.join(OUTPUT_DIR, "demo_video_clean.webm")
    if os.path.exists(dst):
        os.remove(dst)
    os.rename(src, dst)
    print(f"✅ Video saved: {dst}", flush=True)
    
    # Convert to mp4 with ffmpeg
    mp4_dst = os.path.join(OUTPUT_DIR, "demo_video_final.mp4")
    if os.path.exists(mp4_dst):
        os.remove(mp4_dst)
    
    import subprocess
    result = subprocess.run([
        "ffmpeg", "-i", dst, 
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-y", mp4_dst
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        size_mb = os.path.getsize(mp4_dst) / (1024 * 1024)
        print(f"✅ MP4 converted: {mp4_dst} ({size_mb:.1f}MB)", flush=True)
    else:
        print(f"❌ FFmpeg conversion failed: {result.stderr[:200]}", flush=True)

if __name__ == "__main__":
    main()

import os
import sys
import time
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

WORK_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = WORK_DIR.parent
HTML_PATH = WORK_DIR / "index.html"
AUDIO_PATH = WORK_DIR / "soundtrack.wav"
FINAL_MP4_PATH = OUTPUT_DIR / "brag.mp4"
POSTER_PATH = OUTPUT_DIR / "brag.jpg"
LOG_PATH = WORK_DIR / "ffmpeg.log"

DURATION = 24.0
FPS = 30
TOTAL_FRAMES = int(DURATION * FPS)
WIDTH = 1920
HEIGHT = 1080

def main():
    print(f"=== RENDERING CONTRACTLLM LAUNCH VIDEO ===")
    print(f"Duration: {DURATION}s | FPS: {FPS} | Total frames: {TOTAL_FRAMES}")
    print(f"HTML: {HTML_PATH}")
    print(f"Audio: {AUDIO_PATH}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        page.goto(HTML_PATH.as_uri())
        page.wait_for_timeout(1500)

        # 1. Capture test stills for inspection
        test_times = [
            (2.0, WORK_DIR / "scene1.jpg"),
            (7.0, WORK_DIR / "scene2.jpg"),
            (12.0, WORK_DIR / "scene3.jpg"),
            (17.0, WORK_DIR / "scene4.jpg"),
            (21.5, WORK_DIR / "scene5.jpg"),
        ]
        print("Capturing scene validation stills...")
        for t, path in test_times:
            page.evaluate(f"window.seek({t})")
            time.sleep(0.05)
            page.screenshot(path=str(path), quality=95, type="jpeg")
            print(f"  Captured {path.name} at {t}s")

        # Save settled poster at t=2.0s
        page.evaluate("window.seek(2.0)")
        time.sleep(0.05)
        page.screenshot(path=str(POSTER_PATH), quality=98, type="jpeg")
        print(f"Saved primary poster to {POSTER_PATH.name}")

        # 2. Launch FFmpeg pipe with mjpeg stream for fast, non-blocking rendering
        log_file = open(LOG_PATH, "w")
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-f", "image2pipe",
            "-vcodec", "mjpeg",
            "-r", str(FPS),
            "-i", "-",
            "-i", str(AUDIO_PATH),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest",
            str(FINAL_MP4_PATH)
        ]

        print(f"Starting FFmpeg pipe stream to {FINAL_MP4_PATH.name}...")
        proc = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=log_file
        )

        t_start = time.time()
        for frame_idx in range(TOTAL_FRAMES):
            t_curr = frame_idx / FPS
            page.evaluate(f"window.seek({t_curr})")
            frame_jpg = page.screenshot(type="jpeg", quality=92)
            try:
                proc.stdin.write(frame_jpg)
            except (BrokenPipeError, OSError) as e:
                print(f"FFmpeg pipe closed unexpectedly at frame {frame_idx}: {e}")
                break

            if (frame_idx + 1) % 60 == 0 or frame_idx == TOTAL_FRAMES - 1:
                elapsed = time.time() - t_start
                fps_render = (frame_idx + 1) / elapsed
                print(f"  Frame {frame_idx + 1}/{TOTAL_FRAMES} ({(frame_idx+1)/TOTAL_FRAMES*100:.1f}%) | {fps_render:.1f} fps")

        proc.stdin.close()
        proc.wait()
        log_file.close()
        browser.close()

    render_time = time.time() - t_start
    print(f"Rendering completed in {render_time:.1f}s.")
    if FINAL_MP4_PATH.exists():
        size_mb = FINAL_MP4_PATH.stat().st_size / (1024 * 1024)
        print(f"SUCCESS: {FINAL_MP4_PATH} ({size_mb:.2f} MB)")
    else:
        print("ERROR: Rendered MP4 not found. Check ffmpeg.log")

if __name__ == "__main__":
    main()

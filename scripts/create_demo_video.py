"""Create 60s demo video from app screenshots + post to X."""
import asyncio
import base64
import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

TMP = tempfile.mkdtemp(prefix="hasha2a_demo_")
BASE = "http://localhost:8080"

SCENES = [
    {
        "url": "/",
        "name": "landing",
        "text": "HashA2A\nBuy Verified Intelligence\nwith HBAR or USDC",
        "duration": 8,
        "sub": "Agent-to-Agent Intelligence Layer on Hedera"
    },
    {
        "url": "/mcp/",
        "name": "mcp",
        "text": "10 MCP Tools\nfor AI Agents",
        "duration": 8,
        "sub": "Model Context Protocol · list_providers · get_price · scan_arbitrage"
    },
    {
        "url": "/dashboard",
        "name": "dashboard",
        "text": "Live Oracle Dashboard",
        "duration": 8,
        "sub": "Multi-oracle aggregation · Real-time spreads · Confidence scoring"
    },
    {
        "url": "/dashboard/oracles",
        "name": "oracles",
        "text": "19 Crypto + Commodity Assets",
        "duration": 8,
        "sub": "Pyth · CoinGecko · DeFiLlama · All verified independently"
    },
    {
        "url": "/.well-known/agent.json",
        "name": "agent_card",
        "text": "A2A Protocol & Agent Discovery",
        "duration": 8,
        "sub": "Google A2A · HCS-10 · /.well-known/agent.json · llms.txt"
    },
    {
        "url": "/api/v1/feeds/x402/manifest",
        "name": "x402_manifest",
        "text": "x402 Dual Rail Payments",
        "duration": 8,
        "sub": "Base USDC · Hedera HBAR/HTS · HIP-1261 Simple Fees"
    },
    {
        "url": "/promo.mp4",
        "name": "promo_bg",
        "text": "",
        "duration": 0,
        "sub": ""
    },
]

def take_screenshot(url, output_path):
    """Take screenshot using Chrome headless."""
    full_url = f"{BASE}{url}"
    print(f"  Screenshotting: {full_url}")
    cmd = [
        "google-chrome", "--headless=new", "--disable-gpu",
        "--no-sandbox", "--disable-dev-shm-usage",
        f"--screenshot={output_path}",
        f"--window-size=1280,720",
        full_url
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=15)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception as e:
        print(f"  Screenshot failed: {e}")
        return False

def add_text_overlay(input_path, output_path, text, sub="", duration=8):
    """Add text overlay to image using ffmpeg."""
    lines = text.split("\n")
    font_size = 48 if len(text) < 20 else 36
    sub_size = 20

    # Build drawtext filters for multi-line text
    filters = []
    y_pos = 80
    for i, line in enumerate(lines):
        filters.append(
            f"drawtext=text='{line}':fontcolor=white:fontsize={font_size}:"
            f"x=(w-text_w)/2:y={y_pos + i * (font_size + 10)}:"
            f"box=1:boxcolor=black@0.6:boxborderw=10:"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        )
    if sub:
        filters.append(
            f"drawtext=text='{sub}':fontcolor=white:fontsize={sub_size}:"
            f"x=(w-text_w)/2:y=h-80:"
            f"box=1:boxcolor=black@0.5:boxborderw=8:"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        )

    # Also add gradient overlay at top for readability
    # Create video with zoompan (Ken Burns effect) and text
    filter_chain = f"zoompan=z='zoom+0.0015':d={duration*30}:fps=30,{','.join(filters)}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", input_path,
        "-t", str(duration),
        "-vf", filter_chain,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast", "-crf", "23",
        output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=30)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 10000
    except Exception as e:
        print(f"  Overlay failed: {e}")
        return False

def create_concat_file(clips, output_path):
    """Create concat file and merge videos."""
    concat_path = os.path.join(TMP, "concat.txt")
    with open(concat_path, "w") as f:
        for clip in clips:
            if os.path.exists(clip) and os.path.getsize(clip) > 10000:
                f.write(f"file '{clip}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", "20",
        "-movflags", "+faststart",
        output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=60)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 50000
    except Exception as e:
        print(f"  Merge failed: {e}")
        return False

async def post_video_to_twitter(video_path, text):
    """Upload video and post tweet."""
    from core.config import Settings
    settings = Settings()

    if not settings.twitter_api_key or not settings.twitter_access_token:
        print("Twitter credentials not configured")
        return False

    import tweepy

    # Use v1.1 API for media upload
    auth = tweepy.OAuth1UserHandler(
        settings.twitter_api_key,
        settings.twitter_api_secret,
        settings.twitter_access_token,
        settings.twitter_access_secret,
    )
    api = tweepy.API(auth)

    # Upload video (chunked for large files)
    print("  Uploading video to Twitter...")
    media = api.media_upload(filename=video_path, media_category="tweet_video")
    print(f"  Media uploaded: {media.media_id}")

    # Post tweet with video
    client = tweepy.Client(
        consumer_key=settings.twitter_api_key,
        consumer_secret=settings.twitter_api_secret,
        access_token=settings.twitter_access_token,
        access_token_secret=settings.twitter_access_secret,
    )

    tweet_text = text[:280] if len(text) > 280 else text
    response = client.create_tweet(text=tweet_text, media_ids=[media.media_id])
    if response and response.data:
        tweet_id = response.data["id"]
        print(f"  Tweet posted: https://x.com/hasha2a/status/{tweet_id}")
        return True
    return False

async def main():
    print("=" * 60)
    print("HashA2A Demo Video Creator")
    print("=" * 60)

    # 1. Take screenshots
    print("\n1. Taking screenshots...")
    screenshots = []
    for scene in SCENES:
        if scene["duration"] == 0:
            continue
        output = os.path.join(TMP, f"{scene['name']}.png")
        ok = take_screenshot(scene["url"], output)
        if ok:
            print(f"   ✓ {scene['name']}")
            screenshots.append(scene)
        else:
            print(f"   ✗ {scene['name']}")

    if not screenshots:
        print("No screenshots taken. Is the app running?")
        return

    # 2. Add text overlays
    print("\n2. Adding text overlays...")
    clips = []
    for scene in screenshots:
        input_img = os.path.join(TMP, f"{scene['name']}.png")
        output_vid = os.path.join(TMP, f"{scene['name']}.mp4")
        ok = add_text_overlay(input_img, output_vid, scene["text"], scene["sub"], scene["duration"])
        if ok:
            clips.append(output_vid)
            print(f"   ✓ {scene['name']} ({scene['duration']}s)")

    # 3. Add promo video if available
    promo_path = os.path.join(os.path.dirname(__file__), "..", "static", "promo.mp4")
    if os.path.exists(promo_path) and os.path.getsize(promo_path) > 100000:
        promo_clip = os.path.join(TMP, "promo_clip.mp4")
        # Take first 12 seconds of promo for the closing
        cmd = [
            "ffmpeg", "-y",
            "-i", promo_path,
            "-t", "12",
            "-vf", "drawtext=text='Open Source':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h/2-60:box=1:boxcolor=black@0.6:boxborderw=10,drawtext=text='github.com/ymiydev-prog/HashA2A':fontcolor=white:fontsize=20:x=(w-text_w)/2:y=h/2+20:box=1:boxcolor=black@0.5:boxborderw=8",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast",
            promo_clip
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
        if os.path.exists(promo_clip) and os.path.getsize(promo_clip) > 10000:
            clips.append(promo_clip)
            print("   ✓ promo closing (12s)")

    # 4. Merge all clips
    print(f"\n3. Merging {len(clips)} clips into final video...")
    output_path = os.path.join(TMP, "hasha2a_demo.mp4")
    ok = create_concat_file(clips, output_path)
    if not ok:
        print("Failed to create final video")
        return

    file_size = os.path.getsize(output_path)
    print(f"   ✓ Video created: {output_path} ({file_size / 1024 / 1024:.1f} MB)")

    # 5. Check duration
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", output_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    duration = float(result.stdout.strip() or 0)
    print(f"   Duration: {duration:.1f}s")

    # 6. Copy to static for easy access
    static_path = os.path.join(os.path.dirname(__file__), "..", "static", "demo.mp4")
    import shutil
    shutil.copy2(output_path, static_path)
    print(f"   Copied to: {static_path}")

    # 7. Post to Twitter
    print("\n4. Posting to Twitter...")
    tweet_text = (
        "🚀 HashA2A — Agent-to-Agent Intelligence Layer on Hedera\n\n"
        "✓ MCP Server with 10 tools\n"
        "✓ x402 Dual Rail (USDC + HBAR)\n"
        "✓ Multi-Oracle Aggregation (19 assets)\n"
        "✓ A2A Protocol + Google A2A compliant\n"
        "✓ Pay-per-query, no API keys\n\n"
        "Open source → github.com/ymiydev-prog/HashA2A\n\n"
        "#Hedera #AI #MCP #x402 #A2A #Agents"
    )
    posted = await post_video_to_twitter(static_path, tweet_text)

    if posted:
        print("\n✓ Demo video posted successfully!")
    else:
        print("\n⚠ Video file ready at static/demo.mp4 but Twitter posting failed")

    # Cleanup
    print(f"\nTemp files in: {TMP}")

if __name__ == "__main__":
    asyncio.run(main())

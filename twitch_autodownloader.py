import json
import subprocess
import os
import time
import streamlink
import sys
import logging
import signal

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

OUTPUT_DIR = "livevods"
live_processes = {}
channel_inferencing = {}

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("download_log.log"),  # Log to this file
                        logging.StreamHandler()  # And also to console
                    ])

def get_stream_url(channel_name, desired_quality):
    try:
        streams = streamlink.streams(f'https://www.twitch.tv/{channel_name}')
        if desired_quality in streams:
            return streams[desired_quality].url
        elif 'best' in streams:
            return streams['best'].url
        else:
            return None
    except Exception as e:
        print(f"Error fetching stream URL for channel {channel_name}: {e}")
        logging.error(f"Error fetching stream URL for channel {channel_name}: {e}")
        return None

def check_channel_status(channel_name, channel_status):
    if channel_status != "inference":
        try:
            streams = streamlink.streams(f'https://www.twitch.tv/{channel_name}')
            if streams:
                return "online"
            else:
                return "offline"
        except Exception as e:
            print(f"Error checking status for channel {channel_name}: {e}")
            logging.error(f"Error checking status for channel {channel_name}: {e}")
            return "error"
    elif channel_status == "inference":
        print(f"Channel {channel_name} is in 'inferencing' state.")
        logging.info(f"Channel {channel_name} is in 'inferencing' state.")
        return "inference"
    else:
        print(f"Unknown status for channel {channel_name}")
        logging.error(f"Unknown status for channel {channel_name}")
        return "unknown"

def generate_output_path(channel_name):
    filename = f"{channel_name}_{time.strftime('%Y%m%d%H%M%S')}"
    return os.path.join(OUTPUT_DIR, filename).replace('\\', '/')

def download_stream(channel_name):
    desired_quality = config["twitch_autodownloader"]["DESIRED_QUALITY"]
    enable_trimming = config["twitch_autodownloader"]["ENABLE_TRIMMING"]
    start_time = config["twitch_autodownloader"]["START_TIME_MINUTES"] * 60
    end_time = config["twitch_autodownloader"]["END_TIME_MINUTES"] * 60
    enable_reencoding = config["twitch_autodownloader"]["ENABLE_REENCODING"]
    reencoding_format = config["twitch_autodownloader"].get("REENCODING_FORMAT", "1080p60")

    # Generate the base output path without suffix
    base_output_path = generate_output_path(channel_name)
    stream_url = get_stream_url(channel_name, desired_quality)

    # Download the full stream
    download_cmd = ["ffmpeg", "-i", stream_url, "-c", "copy", "-bsf:a", "aac_adtstoasc", base_output_path + ".mp4"]
    logging.info(f"Downloading VOD for {channel_name} using the following command/n {download_cmd}")
    run_command(channel_name, download_cmd, base_output_path + ".log")

    modified_output_path = base_output_path + ".mp4"

    # Trim the video if enabled
    if enable_trimming:
        if not os.path.exists(modified_output_path):
            logging.error(f"Original file not found for trimming: {modified_output_path}")
            return None
        trimmed_output_path = base_output_path + "-t.mp4"
        trimmed_log_path = base_output_path + "-t.log"
        trim_cmd = [
            "ffmpeg", "-i", modified_output_path, "-c", "copy",
            "-ss", str(start_time), "-to", str(end_time),
            "-ignore_chapters", "1",
            trimmed_output_path
        ]
        
        logging.info(f"Trimming command: {trim_cmd}")
        return_code, _, _ = run_command(channel_name, trim_cmd, trimmed_log_path)
        if return_code is not None and return_code != 0:
            logging.error(f"Trimming failed for {trimmed_output_path}")
            return None  # or handle error as appropriate

        logging.info(f"Trimming the VOD file at {modified_output_path} and saving it as {trimmed_output_path}")
        modified_output_path = trimmed_output_path
    
    # Re-encode the video if enabled
    if enable_reencoding:
        if not os.path.exists(modified_output_path):
            logging.error(f"Expected trimmed file not found: {modified_output_path}")
            return None  # or handle error as appropriate
        reencoded_output_path = base_output_path + "-tr.mp4" if enable_trimming else base_output_path + "-r.mp4"
        reencoded_log_path = base_output_path + "-tr.log" if enable_trimming else base_output_path + "-r.log"
        resolution, frame_rate = parse_reencoding_format(reencoding_format)
        reencode_cmd= [
            'ffmpeg', 
            '-i', modified_output_path,
            '-vf', f'scale=-2:{resolution}',
            '-r', str(frame_rate),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'aac',
            '-strict', 'experimental',
            reencoded_output_path
        ]
        logging.info(f"Reencoding the VOD file at {modified_output_path} and saving it as {reencoded_output_path}")
        run_command(channel_name, reencode_cmd, reencoded_log_path)
        if enable_trimming:
            logging.info(f"Trimming was enabled, deleting the video file at {trimmed_output_path}")
            if os.path.exists(trimmed_output_path):
                os.remove(trimmed_output_path)
            if os.path.exists(trimmed_log_path):
                os.remove(trimmed_log_path)
        modified_output_path = reencoded_output_path

    logging.info(f"Returning the video file {modified_output_path}")
    return modified_output_path

def stop_download(channel_name):
    if channel_name in live_processes:
        process = live_processes[channel_name]
        print(f"Stopping download for {channel_name}. Process ID: {process.pid}")
        logging.info(f"Stopping download for {channel_name}. Process ID: {process.pid}")

        try:
            # Send CTRL_BREAK_EVENT to the process group
            if sys.platform == "win32":
                os.kill(process.pid, subprocess.signal.CTRL_BREAK_EVENT)
            else:
                process.send_signal(subprocess.signal.SIGINT)

            process.wait(timeout=10)  # Wait for the process to terminate

        except subprocess.TimeoutExpired:
            print(f"Timeout expired. Force terminating {channel_name}")
            process.terminate()
        except Exception as e:
            print(f"Error while stopping process: {e}")
            process.terminate()

        # Remove the process from the dictionary
        del live_processes[channel_name]

def parse_reencoding_format(format_string):
    parts = format_string.lower().split('p')
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        return (int(parts[0]), int(parts[1]))
    else:
        raise ValueError(f"Invalid re-encoding format: {format_string}")

def run_command(channel_name, cmd, log_file_path):
    with open(log_file_path, "w") as stderr_file:
        process = subprocess.Popen(cmd, stderr=stderr_file, stdout=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        live_processes[channel_name] = process

        try:
            stdout, stderr = process.communicate()
        except subprocess.TimeoutExpired:
            logging.error(f"Timeout expired for command: {cmd}")
            process.kill()
            stdout, stderr = process.communicate()

        return_code = process.returncode
        if return_code != 0:
            logging.error(f"Command failed with return code {return_code}. Command: {cmd}")
        return return_code, stdout, stderr

def get_reencode_command(input_path, output_path, format_string):
    resolution, frame_rate = parse_reencoding_format(format_string)
    reencode_cmd = [
        'ffmpeg',
        '-i', input_path,
        '-vf', f'scale=-2:{resolution}',
        '-r', str(frame_rate),
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-c:a', 'aac',
        '-strict', 'experimental',
        output_path
    ]

if __name__ == "__main__":
    # Example usage
    channel = "example_channel"
    if check_channel_status(channel) == "online":
        download_stream(channel)
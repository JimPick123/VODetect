# VODetect

VODetect is a powerful tool designed to download videos from YouTube and Twitch VODs, and then process them using a pretrained YOLOv8 model to detect objects. This project is an experimental exercise in using ChatGPT to code a complex program, and as such it has been nearly 100% written by ChatGPT. Due to this, do not expect the code to be pretty or entirely bug-free. If you encounter a bug feel free to open an issue, but I cannot guarantee it will be resolved. For those who wish to tackle the challenge of repairing/improving the code themselves, feel free to fork this.

## Features

- **Video Downloading**: Easily download videos from YouTube or Twitch VODs.
- **Object Detection**: Uses a pretrained YOLOv8 model to detect and identify objects within the videos.
- **Batch Processing**: Process multiple videos in a directory with ease.
- **Custom Configuration**: Adjust settings and parameters via a configuration file.
- **Cross-Platform**: Works on both Windows and Linux.

## Installation

### Prerequisites

- Python 3.10 or higher
- Virtual Environment (recommended)

### Installation

1. Clone the repository:
``https://github.com/rrweller/VODetect``

2. Visit https://pytorch.org/get-started/locally/ and copy the correct installation command for your installed version of CUDA *THIS IS VERY IMPORTANT AS TORCH IS A PAIN*
   - The program will default to using the CPU if mismatched versions of CUDA and torch are installed. If you have extremely slow inference this is why

4. Edit the install.bat or install.sh file and replace the ``pip3 install torch torchvision torchaudio`` line with the install command you copied

5. Run the ``install.bat`` or ``install.sh`` file

6. Create a folder named "model" and place your YOLO .pt model file into that directory

7. If you intend on using the Twitch functionality, edit ``request_oauth.py`` and add your CLIENT ID and CLIENT SECRET. Run this script and copy the OAUTH key it provides you

8. Rename ``exampleconfig.json`` to ``config.json`` and open it

9. Paste your OAUTH key into the config file, specify the name of your YOLO model file, and modify any other values you desire. Refer to the description of these settings below

10. Run ``run.bat`` or ``run.sh``


## Configuration Settings

### Processor
- **MAX_INFERENCE_THREADS**: The maximum number of threads that can run inference simultaneously. This determines how many videos can be processed at the same time.
  - What you choose to set this at will vary with your GPU and how large your model is. Some amount of threading is ideal as in most cases inference does not fully use the GPU with a single thread, however you will hit diminishing returns quickly. I recommend setting this between 2-4

### Folder Processing
- **VIDEO_RESOLUTION**: The target resolution `[width, height]` to which all videos in a directory will be resized to when the script is in folder processing mode.
- **RESIZE_VIDEOS**: Enables or disabled video resizing

### Twitch Downloader
- **CLIENT_ID**: Your Twitch application's client ID. This is required to make API requests to Twitch.
- **OAUTH_TOKEN**: Your Twitch OAuth token. This is required for authentication when making certain API requests to Twitch. Use the `request_oauth.py` script to obtain one.
- **DESIRED_QUALITY**: The desired quality/resolution of the Twitch VODs you want to download (e.g., "720p").
  - Valid values are ``1080p``,``720p``,``480p``,and ``360p``,
- **ENABLE_TRIMMING**: Enables VOD trimming to avoid processing an entire VOD
- **START_TIME_MINUTES**: Chooses the start time in minutes of the VOD to trim at
- **END_TIME_MINUTES**: Chooses the end time in minutes of the VOD to end trimming at

### Twitch Auto-downloader
- **AUTO_START_TWITCH_AUTODOWNLOADER**: If set to true, the program will automatically start the Twitch auto-downloader when launched.
- **ENABLE_TRIMMING**: Boolean option to enable or disable trimming of the downloaded Twitch streams.
- **START_TIME_MINUTES and END_TIME_MINUTES**: Define the start and end times for stream trimming, in minutes.
- **ENABLE_REENCODING**: When set to true, the program will reencode the downloaded stream to the specified format.
- **REENCODING_FORMAT**: Defines the resolution and framerate for reencoding. The format should be specified as "{resolution}p{framerate}" (e.g., "720p30" for 720p resolution at 30 frames per second).
- **channels**: A list of channel names to monitor and download streams from.
- **CHECK_INTERVAL_SECONDS**: The time interval, in seconds, at which the program checks the status of the specified Twitch channels.

### YouTube Downloader
- **DESIRED_QUALITY**: The desired quality/resolution of the YouTube videos you want to download (e.g., "720p").
  - Valid values are ``1080p``,``720p``,``480p``,and ``360p``,

### Inference
- **model_path**: The path to the pretrained YOLO model that will be used for object detection.
- **output_dir**: The directory where the inference results will be saved.
- **debug**: If set to `true`, the program will run in debug mode. Costs performance!
  - Debug mode draws the bounding boxes over the output videos, and also outputs an entire full length video in the debug folder.
- **log_output_only**: If set to `true`, only the object detections that were output will be logged. Set to `false` to write all object detections by the model to the log.
- **frame_check_interval**: Runs the model on every `n-th` frame. Useful for increasing performance with some accuracy loss. Valid values are positive integers.
- **grace_period_val**: The number of frames to wait before declaring that an object is no longer in the video. Useful to prevent false negatives from prematurely ending the object dection window.
  - The ideal value varies based on the `frame_check_interval`. I recommend a value of `4-6` for an interval of `2`
- **min_detect_percent**: The minimum percentage of frames in which an object must be detected in its window to be considered present in the video. Helps eliminate false positives. Valid values are from `0-1`
- **default_confidence_threshold**: The default confidence threshold for object detection. Objects detected with a confidence below this threshold will be ignored. Valid values are from `0-1`
- **user_defined_confidence_thresholds**: Specific confidence thresholds for certain objects. If you want to have a higher threshold for a specific object, you can set it here. Valid values are from `0-1`
- **enable_preprocessing**: If set to `true`, the video will undergo a histogram transformation as a pre-processing step. Useful if your video is abnormally dark. Off by default
- **histogram_equalization_weight**: The weight for histogram equalization during preprocessing. This enhances the contrast of the video, which can improve object detection in certain scenarios. Valid values are from `0-1`.

## Model training
If you wish to train your own YOLO model, I recommend using https://roboflow.com/. You can use their service for free to tag objects in your training images and export the dataset. They also provide free to use Google Colab notebooks to train your model using the exported dataset.

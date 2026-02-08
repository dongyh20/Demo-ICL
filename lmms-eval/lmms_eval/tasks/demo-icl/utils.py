import datetime
import json
import os
import random
import sys
from pathlib import Path
import yaml
import re
try:
    import ffmpeg
except ImportError:
    print("ffmpeg is not installed, please install it using 'pip install ffmpeg-python'")
    sys.exit(1)

import lmms_eval.tasks._task_utils.file_utils as file_utils

video_cache_dir = "demo-icl/video_cache"
interleave_cache_dir = "demo-icl/interleave_video_cache"
with open(Path(__file__).parent / "_default_template_yaml", "r") as f:
    raw_data = f.readlines()
    safe_data = []
    for i, line in enumerate(raw_data):
        # remove function definition since yaml load cannot handle it
        if "!function" not in line:
            safe_data.append(line)

    config = yaml.safe_load("".join(safe_data))

# We will unzip all the zip files
# To HF HOME cache dir
# And load it here
HF_HOME = os.environ["HF_HOME"] if "HF_HOME" in os.environ else os.path.expanduser("~/.cache/huggingface")
cache_dir = config["dataset_kwargs"]["cache_dir"]
cache_dir = os.path.join(HF_HOME, cache_dir)

from loguru import logger as eval_logger


def has_audio(path):
    try:
        probe = ffmpeg.probe(path)
        audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']
        return len(audio_streams) > 0
    except ffmpeg.Error as e:
        print(f"Error probing {path}: {e.stderr.decode('utf-8')}")
        return False

def doc_to_visual_interleave(doc):
    source_file = doc['source_id'] + ".mp4"
    target_file = doc["target_id"] + ".mp4"
    source_path = os.path.join(cache_dir, source_file)
    target_path = os.path.join(cache_dir, target_file)
    
    # Check if the video path exists, if not, try replacing the case
    if not os.path.exists(source_path):
        alt_source_path = source_path.replace(".mp4", ".MP4")
        if os.path.exists(alt_source_path):
            source_path = alt_source_path
        else:
            sys.exit(f"video path:{source_path} does not exist, please check")
    
    if not os.path.exists(target_path):
        alt_target_path = target_path.replace(".mp4", ".MP4")
        if os.path.exists(alt_target_path):
            target_path = alt_target_path
        else:
            sys.exit(f"video path:{target_path} does not exist, please check")
    
    # Output directory
    if not os.path.exists(interleave_cache_dir):
        os.makedirs(interleave_cache_dir, exist_ok=True)
    
    output_path = os.path.join(interleave_cache_dir, f"{doc['id']}.mp4")
    if os.path.exists(output_path):
        return [output_path]
    
    target_end_time = doc["start_time"]
    
    # Unified parameters
    unified_width = 640
    unified_height = 360
    unified_fps = 30
    
    # Create input streams
    source_in = ffmpeg.input(source_path)
    target_in = ffmpeg.input(target_path, ss=0, t=target_end_time)
    
    # Process videos uniformly: frame rate, resolution
    source_video = source_in.video.filter('fps', fps=unified_fps).filter('scale', unified_width, unified_height)
    target_video = target_in.video.filter('fps', fps=unified_fps).filter('scale', unified_width, unified_height)
    
    # Check if there are audio streams
    source_audio_exists = has_audio(source_path)
    target_audio_exists = has_audio(target_path)
    
    if source_audio_exists and target_audio_exists:
        source_audio = source_in.audio
        target_audio = target_in.audio
        concat_node = ffmpeg.concat(source_video, source_audio, target_video, target_audio, v=1, a=1).node
        output_video = concat_node[0]
        output_audio = concat_node[1]
        ff_output = ffmpeg.output(output_video, output_audio, output_path,
                                    pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast', hwaccel='cpu')
    else:
        # Concatenate video streams only
        concat_node = ffmpeg.concat(source_video, target_video, v=1, a=0).node
        output_video = concat_node[0]
        ff_output = ffmpeg.output(output_video, output_path,
                                    pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast', hwaccel='cpu')
    
    try:
        ff_output.overwrite_output().run(capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        print("FFmpeg error output:")
        print(e.stderr.decode('utf-8'))
        sys.exit(1)
    
    print(f"\033[92mVideos {source_path} and {target_path} merged successfully to {output_path}\033[0m")
    return [output_path]

def doc_to_visual(doc):
    video_filename = doc["id"] + ".mp4"
    video_path = os.path.join(cache_dir, video_filename)
    
    if not os.path.exists(video_path):
        alt_video_path = video_path.replace(".mp4", ".MP4")
        if os.path.exists(alt_video_path):
            video_path = alt_video_path
        else:
            sys.exit(f"video path:{video_path} does not exist, please check")

    if not os.path.exists(video_cache_dir):
        os.makedirs(video_cache_dir, exist_ok=True)

    # use ffmpeg to slice the video
    output_path = os.path.join(video_cache_dir, f"{doc['id']}.mp4")
    if os.path.exists(output_path):
        return [output_path]
    start_time = 0
    end_time = doc["start_time"]

    (
        ffmpeg
        .input(video_path, ss=start_time, to=end_time)
        .output(output_path, pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast', hwaccel='cpu')
        .overwrite_output()
        .run()
    )
    print(f"\033[92mVideo {video_path} sliced successfully to {output_path}\033[0m")

    return [output_path]


# This is the place where you format your question
def doc_to_text(doc, lmms_eval_specific_kwargs=None):
    number_to_alphabet = {
        0: "A",
        1: "B",
        2: "C",
        3: "D",
    }
    if lmms_eval_specific_kwargs is None:
        lmms_eval_specific_kwargs = {}
    pre_prompt = ""
    post_prompt = ""
    if "pre_prompt" in lmms_eval_specific_kwargs:
        pre_prompt = lmms_eval_specific_kwargs["pre_prompt"]
    if "post_prompt" in lmms_eval_specific_kwargs:
        post_prompt = lmms_eval_specific_kwargs["post_prompt"]

    question = doc["question"]
    for idx, choice in enumerate(doc["choices"]):
        question += "\n" + number_to_alphabet[idx] + ". " + (choice)
    post_prompt = "\nAnswer with the option's letter from the given choices directly."

    return f"{pre_prompt}{question}{post_prompt}"

def extract_characters_regex(s):
    s = s.strip()
    answer_prefixes = [
        "The best answer is",
        "The correct answer is",
        "The answer is",
        "The answer",
        "The best option is" "The correct option is",
        "Best answer:" "Best option:",
    ]
    for answer_prefix in answer_prefixes:
        s = s.replace(answer_prefix, "")

    if len(s.split()) > 10 and not re.search("[ABCD]", s):
        return ""

    matches = re.search(r"[ABCD]", s)
    if matches is None:
        return ""
    return matches[0]
    
# Process result for mc_ppl
def process_results(doc, results):
    pred = results[0]
    pred_ans = extract_characters_regex(pred)
    # gt_ans = doc["answer"].lower().strip().replace(".", "")
    doc["pred_answer"] = pred_ans
    number_to_alphabet = {
        0: "A",
        1: "B",
        2: "C",
        3: "D",
    }
    ground_truth = random.choice(["A", "B", "C", "D"])
    for idx, choice in enumerate(doc["choices"]):
        if choice == doc["answer"]:
            ground_truth = number_to_alphabet[idx]
    doc["ground_truth"] = ground_truth
    data_dict = doc.copy()
    return {f"mcq_accuracy":data_dict}



def aggregate_score(results, args):
    yes_count = 0
    # results is a list of dict
    for answer_dict in results:
        if str(answer_dict["ground_truth"]) == str(answer_dict["pred_answer"]):
            yes_count = yes_count + 1

    accuracy = yes_count / len(results)

    return accuracy

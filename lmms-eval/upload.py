from huggingface_hub import HfApi
from datasets import load_dataset, Dataset
import json
import os

# Initialize Hugging Face API
api = HfApi()

# Define file path and target repository
file_path = "yuhao.zip"
repo_id = "Choiszt/yuhao"  # Replace with your Hugging Face username and repository name

# Upload zip file to Hugging Face Hub
def upload_zip_file():
    try:
        # Create dataset repository (if it doesn't exist)
        api.create_repo(
            repo_id=repo_id,
            repo_type="dataset",  # Specify as dataset type
            private=True,  # Set as private repository, modify as needed
            token=None,  # If logged in, token is not needed; otherwise, provide your HF_TOKEN
        )
        print(f"✅ Dataset repository {repo_id} created or already exists")
        
        # Upload file to dataset repository
        api.upload_file(
            path_or_fileobj=file_path,
            path_in_repo=file_path,
            repo_id=repo_id,
            repo_type="dataset",  # Specify as dataset type
            token=None,  # If logged in, token is not needed; otherwise, provide your HF_TOKEN
        )
        print(f"✅ File {file_path} successfully uploaded to dataset {repo_id}")
    except Exception as e:
        print(f"❌ Failed to upload zip file: {e}")

# Upload datasets to Hugging Face Hub
def upload_datasets():
    # Define dataset paths
    # instruct_datasets_path = "data/text-data-instruct-test.json"
    # wo_instruct_datasets_path = "data/text-data-wo-instruct-test.json"
    # video2video_datasets_path = "data/video2video-data-test.json"
    video_wo_instruct_datasets_path = "data/video_wo_instruct.json"
    try:
        # Check if files exist
        # if not os.path.exists(instruct_datasets_path) or not os.path.exists(wo_instruct_datasets_path):
        #     print("❌ Dataset files do not exist, please check the paths")
        #     return

        # # Load datasets with instructions
        # with open(instruct_datasets_path, 'r') as f:
        #     instruct_data = json.load(f)
            
        # with open(wo_instruct_datasets_path, 'r') as f:
        #     wo_instruct_data = json.load(f)
            
        # with open(video2video_datasets_path, 'r') as f:
        #     video2video_data = json.load(f)
        with open(video_wo_instruct_datasets_path, 'r') as f:
            video_wo_instruct_data = json.load(f)
        
        # Convert to Dataset objects
        # Since JSON is a list, convert it to a format suitable for Dataset
        # instruct_dataset = Dataset.from_list(instruct_data)
        # wo_instruct_dataset = Dataset.from_list(wo_instruct_data)
        # video2video_dataset = Dataset.from_list(video2video_data)
        video_wo_instruct_dataset = Dataset.from_list(video_wo_instruct_data)
        # Upload subset of datasets with instructions
        # instruct_dataset.push_to_hub(
        #     repo_id=repo_id,
        #     config_name="text_demo",
        #     split="test",
        # )
        # print(f"✅ Subset text_demo successfully uploaded to {repo_id}")

        # wo_instruct_dataset.push_to_hub(
        #     repo_id=repo_id,
        #     config_name="yuhao_wo_instruct",
        #     split="test",
        # )
        # print(f"✅ Subset yuhao_wo_instruct successfully uploaded to {repo_id}")

        # video2video_dataset.push_to_hub(
        #     repo_id=repo_id,
        #     config_name="video_demo",
        #     split="test",
        # )
        # print(f"✅ Subset video_demo successfully uploaded to {repo_id}")
        video_wo_instruct_dataset.push_to_hub(
            repo_id=repo_id,
            config_name="video_demo_wo_instruct",
            split="test",
        )
        print(f"✅ Subset video_demo_wo_instruct successfully uploaded to {repo_id}")
    except Exception as e:
        print(f"❌ Failed to upload datasets: {e}")
# Execute upload operations
if __name__ == "__main__":
    # print("🚀 Starting zip file upload...")
    # upload_zip_file()
    
    print("\n🚀 Starting dataset upload...")
    upload_datasets()
    
    print("\n✨ All operations completed!")
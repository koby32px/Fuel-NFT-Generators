import json
import os
from pathlib import Path
from tqdm import tqdm

def update_ipfs_cid(metadata_dir, ipfs_cid):
    """
    Update all metadata files in the directory with the actual IPFS CID
    """
    metadata_path = Path(metadata_dir)
    
    if not metadata_path.exists():
        raise Exception(f"Directory {metadata_dir} not found!")

    # Get all JSON files
    json_files = list(metadata_path.glob("*.json"))
    total_files = len(json_files)
    
    print(f"Found {total_files} metadata files to update")
    
    # Update each file
    for json_file in tqdm(json_files, desc="Updating metadata files"):
        # Read the metadata file
        with open(json_file, 'r') as f:
            metadata = json.load(f)
        
        # Update the IPFS CID in the image URL
        metadata['image'] = f"ipfs://{ipfs_cid}/{json_file.stem}.png"
        
        # Save the updated metadata
        with open(json_file, 'w') as f:
            json.dump(metadata, f, indent=2)

def main():
    # Directory containing your metadata JSON files
    metadata_dir = "output/metadata"
    
    # Get IPFS CID from user
    print("\nPlease enter your IPFS CID for the images folder:")
    ipfs_cid = input().strip()
    
    try:
        update_ipfs_cid(metadata_dir, ipfs_cid)
        print("\nSuccess! All metadata files have been updated with the new IPFS CID.")
        
        # Show sample of updated metadata
        print("\nChecking a sample metadata file (1.json):")
        with open(os.path.join(metadata_dir, "1.json"), 'r') as f:
            sample = json.load(f)
            print(f"Sample image URL: {sample['image']}")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()

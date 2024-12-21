import json
import os
from tqdm import tqdm
from pathlib import Path

def verify_metadata(metadata):
    """Verify that metadata has all required fields"""
    required_fields = ["id", "name", "symbol", "description", "image", "background_color", "attributes"]
    missing_fields = [field for field in required_fields if field not in metadata]
    return len(missing_fields) == 0, missing_fields

def combine_metadata(input_folder, output_file):
    combined_metadata = []
    input_path = Path(input_folder)
    
    if not input_path.exists():
        raise Exception(f"Input folder {input_folder} not found!")
    
    # Get all JSON files in the input folder
    json_files = list(input_path.glob("*.json"))
    
    if not json_files:
        raise Exception(f"No JSON files found in {input_folder}")
    
    # Sort the files numerically
    json_files.sort(key=lambda x: int(x.stem))
    
    print(f"Combining {len(json_files)} metadata files...")
    
    # Track any files with issues
    problematic_files = []
    
    # Iterate through each JSON file
    for file_path in tqdm(json_files, desc="Processing"):
        try:
            with open(file_path, 'r') as file:
                metadata = json.load(file)
            
            # Verify metadata structure
            is_valid, missing_fields = verify_metadata(metadata)
            if not is_valid:
                problematic_files.append(f"{file_path.name} (Missing fields: {', '.join(missing_fields)})")
                continue
            
            combined_metadata.append(metadata)
            
        except json.JSONDecodeError:
            problematic_files.append(f"{file_path.name} (Invalid JSON)")
        except Exception as e:
            problematic_files.append(f"{file_path.name} (Error: {str(e)})")
    
    if problematic_files:
        print("\nWarning: Issues found in some files:")
        for file in problematic_files:
            print(f"- {file}")
    
    if not combined_metadata:
        raise Exception("No valid metadata files to combine!")
    
    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the combined metadata to the output file
    with open(output_path, 'w') as outfile:
        json.dump(combined_metadata, outfile, indent=2)
    
    print(f"\nSuccessfully combined {len(combined_metadata)} metadata files")
    print(f"Combined metadata saved to {output_file}")
    
    # Print basic stats
    print("\nCollection Statistics:")
    print(f"Total NFTs: {len(combined_metadata)}")
    trait_types = set()
    for metadata in combined_metadata:
        for trait in metadata.get("attributes", []):
            trait_types.add(trait.get("trait_type"))
    print(f"Trait Types: {', '.join(sorted(trait_types))}")

def main():
    try:
        input_folder = "output/metadata"
        output_file = "combine_metadata.json"
        combine_metadata(input_folder, output_file)
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
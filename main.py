import json
import random
from PIL import Image
import os
import hashlib
from tqdm import tqdm
from collections import defaultdict, Counter, OrderedDict

class TraitTracker:
    def __init__(self):
        self.trait_patterns = defaultdict(int)
        self.bsh_combinations = set()
        self.MAX_SIMILAR_COMBINATIONS = 1

    def get_trait_pattern(self, traits):
        patterns = []
        trait_items = list(traits.items())
        
        if len(trait_items) >= 4:
            for i in range(len(trait_items) - 3):
                for j in range(i + 1, len(trait_items) - 2):
                    for k in range(j + 1, len(trait_items) - 1):
                        for l in range(k + 1, len(trait_items)):
                            pattern = tuple(sorted([
                                trait_items[i],
                                trait_items[j],
                                trait_items[k],
                                trait_items[l]
                            ]))
                            patterns.append(pattern)
        return patterns

    def get_bsh_combination(self, traits):
        if all(t in traits for t in ['Base', 'Suit', 'Head']):
            return (
                traits['Base'],
                traits['Suit'],
                traits['Head']
            )
        return None

    def is_unique_enough(self, traits):
        bsh_combo = self.get_bsh_combination(traits)
        if bsh_combo and bsh_combo in self.bsh_combinations:
            return False

        patterns = self.get_trait_pattern(traits)
        return all(self.trait_patterns[pattern] < self.MAX_SIMILAR_COMBINATIONS 
                  for pattern in patterns)

    def update_patterns(self, traits):
        patterns = self.get_trait_pattern(traits)
        for pattern in patterns:
            self.trait_patterns[pattern] += 1
            
        bsh_combo = self.get_bsh_combination(traits)
        if bsh_combo:
            self.bsh_combinations.add(bsh_combo)

class NFTGenerator:
    SPECIAL_TRAITS = ["DB Saiyan"]
    MAX_ATTEMPTS = 1000
    MAX_TRAIT_ATTEMPTS = 100
    
    # Background colors list
    BACKGROUND_COLORS = [
        "2eebb1", "9bb5ff", "27e174", "74d9dc", "9175fd", 
        "b281f6", "c4ffe3", "d2dfe7", "f0cb9f", "f6f87b", 
        "fb3d69", "fe81c5", "fe9137", "fedc60", "ff9dcd", 
        "ffd7d8", "fff6d7"
    ]

    def __init__(self, config_file, ruler_file):
        self.config = self.load_json(config_file)
        self.ruler = self.load_json(ruler_file)
        self.trait_order = self.config["trait_order"]
        self.traits = self.config["traits"]
        self.setup_directories()
        self.tracker = TraitTracker()
        self.generated_hashes = set()
        self.failed_attempts = Counter()

    def setup_directories(self):
        self.output_dir = "output"
        self.metadata_dir = os.path.join(self.output_dir, "metadata")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)

    def load_json(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    def get_random_background_color(self):
        """Get a random background color from the list"""
        return random.choice(self.BACKGROUND_COLORS)

    def should_include_trait(self, trait_type):
        return random.random() * 100 < self.traits[trait_type]["rarity"]

    def select_trait(self, options):
        total_rarity = sum(option["rarity"] for option in options)
        random_value = random.uniform(0, total_rarity)
        cumulative_rarity = 0

        for option in options:
            cumulative_rarity += option["rarity"]
            if random_value <= cumulative_rarity:
                return option

    def is_valid_trait(self, selected_traits, new_trait_type, new_trait_value):
        for rule in self.ruler["rules"]:
            if_condition = rule["if"]
            then_condition = rule["then"]
            
            if if_condition["trait_type"] == new_trait_type:
                if new_trait_value in if_condition["value"]:
                    excluded_trait_type = then_condition["trait_type"]
                    if excluded_trait_type in selected_traits:
                        excluded_value = selected_traits[excluded_trait_type]
                        if excluded_value in then_condition["excluded_values"] or "all" in then_condition["excluded_values"]:
                            return False

            if if_condition["trait_type"] in selected_traits:
                existing_value = selected_traits[if_condition["trait_type"]]
                if existing_value in if_condition["value"]:
                    if then_condition["trait_type"] == new_trait_type:
                        if new_trait_value in then_condition["excluded_values"] or "all" in then_condition["excluded_values"]:
                            return False
        return True

    def generate_nft(self, nft_id):
        for _ in range(self.MAX_ATTEMPTS):
            traits = OrderedDict()
            valid_combination = True
            
            priority_traits = ['Base', 'Suit', 'Head']
            remaining_traits = [t for t in self.trait_order if t not in priority_traits]
            generation_order = priority_traits + remaining_traits

            for trait_type in generation_order:
                if self.should_include_trait(trait_type):
                    valid_trait = False
                    for _ in range(self.MAX_TRAIT_ATTEMPTS):
                        trait = self.select_trait(self.traits[trait_type]["options"])
                        if self.is_valid_trait(traits, trait_type, trait["name"]):
                            traits[trait_type] = trait["name"]
                            valid_trait = True
                            break
                    
                    if not valid_trait:
                        valid_combination = False
                        self.failed_attempts['trait_validation'] += 1
                        break

            if valid_combination and self.tracker.is_unique_enough(traits):
                nft_hash = hashlib.sha256(json.dumps(traits, sort_keys=True).encode()).hexdigest()
                if nft_hash not in self.generated_hashes:
                    self.generated_hashes.add(nft_hash)
                    self.tracker.update_patterns(traits)
                    return traits, nft_hash
            else:
                self.failed_attempts['uniqueness'] += 1

        raise Exception(f"Failed to generate unique NFT after {self.MAX_ATTEMPTS} attempts")

    def save_nft(self, traits, nft_id, nft_hash):
        # Image generation
        base_image = Image.new("RGBA", (960, 960), (255, 255, 255, 0))
        modified_order = (["Base", "Suit", "Mouth", "Head", "Eyes"] 
                         if "Head" in traits and traits["Head"] in self.SPECIAL_TRAITS 
                         else self.trait_order)

        for trait_type in modified_order:
            if trait_type in traits:
                layer_path = f"traits/{trait_type}/{traits[trait_type]}.png"
                try:
                    layer_image = Image.open(layer_path)
                    base_image = Image.alpha_composite(base_image, layer_image)
                except Exception as e:
                    print(f"Error loading image {layer_path}: {str(e)}")
                    raise

        base_image.save(f"{self.output_dir}/{nft_id}.png")

        # Get random background color
        background_color = self.get_random_background_color()

        # Thunder/Fuel compatible metadata structure
        metadata = {
            "id": str(nft_id),
            "name": f"Koby #{nft_id}",
            "symbol": "KOBY",
            "description": "32x32 Pixel Unique NFT Collection",
            "image": f"ipfs://<your-ipfs-cid>/{nft_id}.png",
            "external_url": "https://github.com/koby32px",
            "background_color": background_color,
            "attributes": [
                {"trait_type": trait_type, "value": traits.get(trait_type, "None")}
                for trait_type in self.trait_order
            ]
        }

        with open(f"{self.metadata_dir}/{nft_id}.json", 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return background_color

    def generate_collection(self, num_nfts):
        collection = []
        print(f"Generating {num_nfts} NFTs...")
        
        # Track background color distribution
        color_distribution = Counter()
        
        for i in tqdm(range(1, num_nfts + 1), desc="Generating NFTs"):
            try:
                nft_traits, nft_hash = self.generate_nft(i)
                background_color = self.save_nft(nft_traits, i, nft_hash)
                color_distribution[background_color] += 1
                
                collection.append({
                    "id": i,
                    "image_name": f"{i}.png",
                    "traits": nft_traits,
                    "hash": nft_hash,
                    "background_color": background_color
                })
            except Exception as e:
                print(f"Failed to generate NFT {i}: {str(e)}")

        self.save_collection_data(collection)
        print(f"Generation complete. Success rate: {len(collection)/num_nfts*100:.2f}%")
        print(f"Failed attempts: {dict(self.failed_attempts)}")
        print("\nBackground color distribution:")
        for color, count in color_distribution.items():
            print(f"#{color}: {count} NFTs ({count/num_nfts*100:.2f}%)")

    def save_collection_data(self, collection):
        with open(f"{self.output_dir}/collection_metadata.json", 'w') as f:
            json.dump(collection, f, indent=2)

        stats = {
            "total_nfts": len(collection),
            "unique_bsh_combinations": len(self.tracker.bsh_combinations),
            "unique_4trait_patterns": len(self.tracker.trait_patterns),
            "generation_failures": dict(self.failed_attempts)
        }
        
        with open(f"{self.output_dir}/collection_stats.json", 'w') as f:
            json.dump(stats, f, indent=2)

def main():
    print("Initializing NFT Generator...")
    generator = NFTGenerator("config.json", "ruler.json")
    num_nfts = 3200
    generator.generate_collection(num_nfts)

if __name__ == "__main__":
    main()
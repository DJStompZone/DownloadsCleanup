import json
import shutil
import os
import argparse

def read_config(config_path):
    """Reads the cleanup configuration file."""
    with open(config_path, encoding='utf-8') as fp:
        return json.load(fp)

def transform_data(data_path):
    """Transforms the list of dictionaries into a structured format."""
    with open(data_path, encoding='utf-8-sig') as fp:
        input_data = json.load(fp)
    transformed_data = {}
    for item in input_data:
        kind = item["Kind"].lower() if item["Kind"] else "none"
        transformed_item = {
            "path": item["Path"].replace("\\", "/"),
            "type": item["Type"],
        }
        if kind not in transformed_data:
            transformed_data[kind] = []
        transformed_data[kind].append(transformed_item)
    return transformed_data

def move_single(src_path, dest_path, strategy="rename"):
    """Moves a single file with the specified strategy."""
    if os.path.exists(dest_path):
        if strategy == "overwrite":
            shutil.move(src_path, dest_path)
        elif strategy == "rename":
            base, extension = os.path.splitext(dest_path)
            counter = 1
            new_dest_path = f"{base}_{counter}{extension}"
            while os.path.exists(new_dest_path):
                counter += 1
                new_dest_path = f"{base}_{counter}{extension}"
            shutil.move(src_path, new_dest_path)
        elif strategy == "skip":
            return
        elif strategy == "raise":
            raise FileExistsError(f"File {dest_path} already exists.")
    else:
        shutil.move(src_path, dest_path)

def move_files(data, config, strategy="rename"):
    """Moves files based on the transformation data and cleanup configuration."""
    for category, settings in config.items():
        if category == "directories":
            continue
        target_path = settings.get("path")
        if not target_path:
            continue
        os.makedirs(target_path, exist_ok=True)
        for kind in settings.get("kinds", []):
            if kind not in data:
                continue
            for item in data[kind]:
                src_path = item["path"].replace("/", "\\")
                filename = os.path.basename(src_path)
                dest_path = os.path.join(target_path, filename)
                print(f"Moving {src_path} to {dest_path}")
                move_single(src_path, dest_path, strategy=strategy)

def get_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Move files according to a cleanup configuration.")
    parser.add_argument("--data", "-d", dest="data_path", type=str, required=True, help="Path to the data JSON file.")
    parser.add_argument("--config", "-c", dest="config_path", type=str, required=False, default="./cleanup.config.json", help="Path to the cleanup configuration JSON file.")
    parser.add_argument("--strategy", "-s", dest="strategy", type=str, required=False, default="rename", choices=["rename", "overwrite", "skip", "raise"], help="Strategy to use when a destination file already exists.")
    args = parser.parse_args()
    return args.config_path, args.data_path, args.strategy

def main():
    config_path, data_path, strategy = get_args()    
    config = read_config(config_path)
    data = transform_data(data_path)
    move_files(data, config, strategy)

if __name__ == "__main__":
    main()

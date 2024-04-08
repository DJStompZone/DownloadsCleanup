import json
import os
import shutil
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest.mock import patch, mock_open, MagicMock

import pytest

import cleanup


@pytest.fixture
def mock_config():
    return {
        "images": {
            "path": "path/to/images",
            "kinds": ["picture"]
        }
    }

@pytest.fixture
def mock_args():
    return ["--data", "data_path.json", "--config", "config_path.json", "--strategy", "rename"]
    
def test_read_config(mock_config):
    """Test reading the configuration file."""
    with patch('cleanup.open', mock_open(read_data=json.dumps(mock_config)), create=True) as mocked_file:
        config = cleanup.read_config('dummy/path')
        mocked_file.assert_called_once_with('dummy/path', encoding='utf-8')
        assert config == mock_config

@pytest.fixture
def mock_data():
    input_data = [
        {
            "Kind":  "Picture",
            "Type":  "PNG File",
            "Path":  "C:\\Users\\squidward\\Downloads\\clarinet.png"
        },
    ]
    output_data = {
        "picture": [
            {
                "path": "C:/Users/squidward/Downloads/clarinet.png",
                "type": "PNG File"
            },
        ]
    }
    return input_data, output_data

def test_transform_data(mock_data):
    """Test the transform_data function for correct transformation."""
    mock_input_data, expected_output_data = mock_data
    mock_data_path = "path/to/mock_input_data.json"
    
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_input_data)), create=True) as mocked_file, \
         patch('json.load', return_value=mock_input_data):
        transformed_data = cleanup.transform_data(mock_data_path)
        assert transformed_data == expected_output_data
        mocked_file.assert_called_with(mock_data_path, encoding='utf-8-sig')

@patch('cleanup.shutil.move')
@patch('cleanup.os.path.exists', return_value=False)
def test_move_single_new_file(mock_exists, mock_move):
    """Test moving a file that does not exist in the destination."""
    cleanup.move_single('src_path', 'dest_path', 'rename')
    mock_move.assert_called_once_with('src_path', 'dest_path')

@patch('cleanup.argparse.ArgumentParser.parse_args')
def test_get_args(mock_parse_args, mock_args):
    """Test command line argument parsing."""
    mock_parse_args.return_value = MagicMock(data_path='data_path.json', config_path='config_path.json', strategy='rename')
    args = cleanup.get_args()
    assert args == ('config_path.json', 'data_path.json', 'rename')


@pytest.fixture
def temporary_file(temporary_dir):
    """Creates a temporary file manually in the specified directory."""
    temp_file_path = os.path.join(temporary_dir, "temp_file.txt")
    with open(temp_file_path, 'w') as temp_file:
        temp_file.write("This is a temporary file.")
    return temp_file_path

@pytest.fixture
def temporary_dir():
    """Creates a temporary directory for testing."""
    with TemporaryDirectory() as tmp_dir:
        yield tmp_dir

@pytest.mark.parametrize("strategy,expected_behavior", [
    ("overwrite", "overwritten"),
    ("rename", "renamed"),
    ("skip", "skipped"),
    ("raise", "exception")
])
def test_move_single(temporary_dir, strategy, expected_behavior):
    src_filename = "source_file.txt"
    src_path = os.path.join(temporary_dir, src_filename)
    with open(src_path, 'w') as f:
        f.write("Source content")
    dest_filename = "dest_file.txt"
    dest_path = os.path.join(temporary_dir, dest_filename)
    if strategy in ["overwrite", "rename", "raise"]:
        with open(dest_path, 'w') as f:
            f.write("This is a test.")

    print(f"Source Path: {src_path}")
    print(f"Destination Path: {dest_path}")

    if strategy == "raise":
        with pytest.raises(FileExistsError):
            cleanup.move_single(src_path, dest_path, strategy)
    if os.path.exists(src_path):
        os.remove(src_path)
    if os.path.exists(dest_path):
        os.remove(dest_path)


def test_move_single_overwrite(temporary_dir):
    src_path = os.path.join(temporary_dir, "source_file.txt")
    with open(src_path, 'w') as src_file:
        src_file.write("Source content")
    dest_path = os.path.join(temporary_dir, "dest_file.txt")
    with open(dest_path, 'w') as dest_file:
        dest_file.write("Destination content")
    cleanup.move_single(src_path, dest_path, "overwrite")
    assert not os.path.exists(src_path), "Source file should not exist after move"
    with open(dest_path, 'r') as dest_file:
        assert dest_file.read() == "Source content", "Destination file should be overwritten with source content"

def test_move_single_rename(temporary_dir):
    src_path = os.path.join(temporary_dir, "source_file_to_rename.txt")
    with open(src_path, 'w') as src_file:
        src_file.write("Source content to be renamed")
    dest_path = os.path.join(temporary_dir, "existing_dest_file.txt")
    with open(dest_path, 'w') as dest_file:
        dest_file.write("Existing destination content")
    cleanup.move_single(src_path, dest_path, "rename")
    assert os.path.exists(dest_path), "Original destination file should still exist"
    with open(dest_path, 'r') as dest_file:
        assert dest_file.read() == "Existing destination content", "Original destination content should remain unchanged"
    files_after = set(os.listdir(temporary_dir)) - {"existing_dest_file.txt"}
    assert len(files_after) == 1, "There should be exactly one new file (the renamed source file)"
    new_file_path = os.path.join(temporary_dir, files_after.pop())
    with open(new_file_path, 'r') as new_file:
        assert new_file.read() == "Source content to be renamed", "Renamed file should contain the original source content"


def test_move_single_no_destination_file(temporary_file, temporary_dir):
    """Test moving a file when the destination does not exist."""
    src = temporary_file
    dest_path = os.path.join(temporary_dir, "non_existent_file.txt")
    cleanup.move_single(src, dest_path, "rename")
    assert os.path.exists(dest_path) and not os.path.exists(src), "File should be moved successfully."
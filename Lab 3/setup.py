import urllib.request
import zipfile
import os

# URL of the zip file
url = "https://cornell.box.com/shared/static/kjhoc9m6wnyncew23bpnfy0ibcbe1hjj.zip"

# Path to the home directory
home_dir = os.path.expanduser("~")

# Download the zip file
zip_file_path = os.path.join(home_dir, "file.zip")
urllib.request.urlretrieve(url, zip_file_path)

# Extract the contents of the zip file
with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
    zip_ref.extractall(home_dir)

# Remove the zip file
os.remove(zip_file_path)

import urllib.request
import zipfile
import os

# URL of the zip file
url = "https://cornell.box.com/shared/static/kjhoc9m6wnyncew23bpnfy0ibcbe1hjj.zip"

# Path to the home directory
home_dir = os.path.expanduser("~")

# Download the zip file
zip_file_path = os.path.join(home_dir, "file.zip")

print("Started downloading...")
urllib.request.urlretrieve(url, zip_file_path)
print("Finished downloading!")

# Extract the contents of the zip file
print("Started unzipping...")
with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
    zip_ref.extractall(home_dir)
print("Finished unzipping!")

# Change the permissions of the files in the folder to executable
extracted_folder = os.path.join(home_dir, os.path.basename(zip_file_path).replace(".zip", ""))
for root, dirs, files in os.walk(extracted_folder):
    for file in files:
        os.chmod(os.path.join(root, file), 0o755)

# Remove the zip file
os.remove(zip_file_path)
print("Zip file removed!")

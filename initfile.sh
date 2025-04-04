# Navigate to the project's root directory (if you're not already there)
cd /home/echeadle/15_DupFiles/

mkdir find-dup-files && cd find-dup-files
# Initialize a Git repository
git init

# Create a .gitignore file
echo ".venv/" > .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".DS_Store" >> .gitignore
echo "config.json" >> .gitignore


# Add all files to the repository
git add .

# Commit the changes with an initial commit message
git commit -m "Initial commit: Project setup and planning files"

# Create a conda environment named 'dupfiles' with Python 3.11
conda create -n dupfiles python=3.11 -y

# Activate the conda environment
conda activate dupfiles

# Install FastAPI and Uvicorn
pip install fastapi uvicorn

# Verify the installation
pip list

# Navigate to the project's root directory (if you're not already there)
cd /home/echeadle/15_DupFiles/find-dup-files/

# Create the directory structure
mkdir -p app/api app/core app/models static tests

# Create placeholder files
touch app/api/routes.py
touch app/core/db.py
touch app/core/scanner.py
touch app/main.py
touch app/models/file_entry.py
touch static/index.html
touch tests/test_placeholder.py
touch config.json


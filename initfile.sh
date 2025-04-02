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

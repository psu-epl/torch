# Check if a virtual environment exists, create it if not, and start it
# Made by Benjamin Crall 2024, GNU General Public License v3.0
VENV=".venv"
echo "$VENV"
# Must start the VENV from either path
if [ -d $VENV ]; then
    echo "Found virtual environment, launching app ..."
    source "$VENV/bin/activate"
else
    # Set up the virtual environment
    echo "No virtual environment found in $VENV. Setting up now ..."
    python -m venv "$VENV"
    if [ "$?" -ne "0" ]; then
        # If the module doesn't exist, then the user needs to install it themselves
        echo "Please install venv then try again. To do this, run:"
        echo "    sudo apt install python3-venv"
        exit
    fi
    # Install dependencies
    echo "Environment created, installing packages"
    source "$VENV/bin/activate"
    pip install -r requirements.txt
    if [ "$?" -ne "0" ]; then
        # If there was an issue, the user needs to address it
        echo "Dependency installation failed, please fix the issue then try again"
        exit
    fi
    echo "Environment created, launching app ..."
fi

# Run the actual
python run.py
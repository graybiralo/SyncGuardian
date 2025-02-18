# PersonalProject

This project monitors folder changes in real-time and notifies connected clients of those changes.

## Setup Instructions

### Prerequisites:
- Python 3.x installed on your machine.
- Git installed.

### Installation:
1. Clone this repository to your local machine:
   ```bash
   git clone git clone <repository_url>
 
2. Create a virtual environment (recommended) to keep the dependencies isolated:
    ```bash
    python3 -m venv venv

3. Activate the virtual environment:
    ```bash
    On Windows:
    venv\Scripts\activate

    On macOS/Linux:
    source venv/bin/activate

4. Install the required dependencies from requirements.txt:
    ```bash
    pip install -r config/requirements.txt

5. Run the application:
    ```bash
    python FolderUpdates/main.py

6. Folder Structure:
    ```bash
    This is the structure of the project:

    SyncGuardian/
    ├── FolderUpdates/
    │   ├── main.py            # Main script to start the server and monitor folder changes
    │   └── folder_selector.py # Script for folder selection
    ├── __pycache/             # Compiled Python bytecode files (auto-generated)
    ├── config/
    │   ├── requirements.txt   # List of required dependencies
    │   └── setup.py           # Setup script for the project
    ├── docs/
    │   └── README.md          # Project documentation
    

## Notes:

    Ensure that you have Python 3.x installed.
    If you're using a virtual environment, activate it before running the project.
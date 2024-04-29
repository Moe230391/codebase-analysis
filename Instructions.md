# Code Base Mirror

This project analyzes and mirrors a codebase, providing insights into its structure, dependencies, and quality metrics.

## Setup

1.Installation Instructions

Clone the repository:
<git clone <https://github.com/Moe230391/codebase-analysis.git>

2.Navigate to the project directory:
cd codebase-analysis

3.Create a virtual environment (optional but recommended):
python -m venv venv

4.Activate the virtual environment:

For Windows:
venv\Scripts\activate

For macOS and Linux:
source venv/bin/activate

5.Install the required dependencies:
pip install -r requirements.txt

6.Configure the script by updating the necessary paths and settings in the main_controller.py file:

Set the root_dir variable to the path of the codebase directory you want to analyze.
Set the output_dir variable to the directory where you want to store the output files.
Set the doc_links_csv variable to the path of the CSV file containing documentation links (if applicable).

7.Run the script:
python main_controller.py

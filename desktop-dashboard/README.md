# GPU Monitor

**GPU Monitor** is a desktop application built with Python and PySide6 that allows you to monitor GPU metrics such as temperature, power usage, memory usage, and more. 

## Features

* Input a URL that provides GPU metric data (e.g., this project style  or ...)
* View a list of available GPUs with color-coded health states:

  * Normal: Healthy
  * Yellow: Warning
  * Red: Error
* Click on each GPU to navigate to a detailed page
* Real-time graphing using matplotlib
* Left-side panel to toggle which metrics to display

## Installation

1. Clone the repository:

   ```
   git clone Path of here
   cd desktop-dashboard
   ```

2. Create and activate a virtual environment:

   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the required Python packages:

   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, provide the URL where GPU metrics can be fetched:

```
python main.py http://localhost:8000/metrics
```

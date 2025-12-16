


# How to run my Meraki Automation Scripts

## Create a environment.env file

In your project directory, create a file named environment.env
Add your API key in the following format:

API_KEY= 'your_actual_api_key_here'
ORG_ID = 'your_organization_id'

Replace your_actual_api_key_here with your real Meraki Dashboard API key.
This approach keeps your API keys out of your source code and makes your scripts more secure and portable.

## Pip install requirements 
pip install required libraries. Commonly used libraries are
import meraki
import os
from datetime import datetime
import json
import pandas as pd
import dotenv
from dotenv import load_dotenv
import openpyxl

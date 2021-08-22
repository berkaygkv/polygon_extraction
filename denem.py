import os
from dotenv import load_dotenv

load_dotenv()

GROUP_NUMBER = os.getenv('GROUP_NUMBER')
GROUP_ID = os.getenv('GROUP_ID')
server = os.getenv('SERVER')
database = os.getenv('DATABASE') 
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

print(server)
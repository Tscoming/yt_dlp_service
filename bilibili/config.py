import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
# 这将搜索当前目录或父目录中的 .env 文件。
load_dotenv()

# 从环境变量中获取 Bilibili 凭证
SESSDATA = os.getenv("BILI_SESSDATA")
BILI_JCT = os.getenv("BILI_JCT")
BUVID3 = os.getenv("BILI_BUVID3")

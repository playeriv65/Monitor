# 摄像头与视频配置
CAMERA = 0
VIRTUAL = 1
FPS_DEFAULT = 30

# 用户及摔倒检测相关配置
USER = "u001"
FALL_TIME = 0.15           # 摔倒所用秒数
INTERVAL = 1.5             # 两次摔倒检测间隔
RELATIVE_DISTANCE = 0.5    # 头部移动相对距离阈值

# 服务相关配置
PORT = 8088

# 进程开关
CAMERA_ON = True
SERVER_ON = True
RECORDER_ON = True

# 新增配置项
PICTURE_DIR = "./picture"
FALL_RECORD_FILE = "fall_record.json"

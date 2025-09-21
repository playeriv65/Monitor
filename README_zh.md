# Monitor

## 项目简介

本项目用于各种动作与行为监测，支持摔倒检测、行为记录与远程访问。基于YOLO姿态识别、OpenCV视频处理和Flask服务，适用于安防、养老等场景。

## 主要功能
- 实时摄像头动作监测
- 摔倒检测与记录
- 图片抓拍与存储
- WebSocket 实时推送监测结果
- Web API 查询与下载记录

## 依赖环境
- Python 3.8+
- opencv-python
- ultralytics
- flask
- flask_sock

## 快速开始
1. 安装依赖：
	```bash
	pip install -r requirements.txt
	```
2. 运行主程序：
	```bash
	python main.py
	```
3. 访问服务：
	- WebSocket: ws://localhost:8088/connect
	- 查询记录: POST http://localhost:8088/checkall
	- 下载图片: http://localhost:8088/download/<filename>

## 目录结构
- main.py：主入口，进程调度
- examiner.py：动作识别与摔倒检测
- recorder.py：图片与记录保存
- server.py：Web服务与接口
- config.py：参数配置
- picture/：图片存储目录
- fall_record.json：摔倒记录

## 说明
- 支持多进程并发，摄像头、服务、记录可独立开关
- 配置项详见 config.py
- YOLO模型文件需放置于根目录

#!/usr/bin/env python
# coding: utf-8

"""
Configuration file for question generation system.
Contains constants, metadata, and configuration settings.
"""

# Scene Configuration
SCENE = "scene1"

# Answer Type Options
ANSWER_TYPE_OPTIONS = ['Space', 'Time', 'Object', 'Action', 'Aggregation', 'Activity', 'Video']

# Metadata Configuration
METADATA = {
    "Space": ["Place", "Pos3D", "Relation"],
    "Time": ["Instant", "Interval", "Duration", "Current", "First", "Last", "Previous", "Next"],
    "Object": ["None", "Type", "Class", "State", "Attribute", "Size"],
    "Action": ["None"],
    "Aggregation": ["Count", "Min", "Max", "Sum", "Avg"],
    "Activity": ["None", "Previous", "Next"],
    "Video": ["Video", "VideoFrame", "Pos2D"]
}

# Query Pattern Configuration
SPACE_OPERATORS = ["x+", "x-", "y+", "y-", "z+", "z-"]
TIME_INTERVAL_OPERATORS = ["< <", "<= <", "< <=", "<= <="]
TIME_DURATION_OPERATORS = ["<", ">", "<=", ">="]

# Camera Options
CAMERA_OPTIONS = ["camera0", "camera1", "camera2", "camera3", "camera4"]

# Aggregation Configuration
AGGREGATION_COUNT_OPTIONS = ["event", "object", "place"]
AGGREGATION_NUMERIC_OPTIONS = ["duration", "size_x", "size_y", "size_z", "pos_x", "pos_y", "pos_z"]
AGGREGATION_SUM_OPTIONS = ["duration"]

# Video Configuration
VIDEO_POS2D_OPTIONS = ["min", "max"]

# Processing Configuration
MAX_CHECK_COUNT = 5  # 最大5回までクエリパターンを生成してチェックする
DEFAULT_LOOP = 150

# File Paths
GENERATED_QUESTIONS_DIR = "generated_questions"
SEEN_COMBINATIONS_FILE = f"{GENERATED_QUESTIONS_DIR}/seen_combinations.pkl"

#!/usr/bin/env python
# coding: utf-8

"""
Query pattern generation logic for different answer types.
Handles the generation of query patterns for Object, Action, Space, Time, Activity, Video, and Aggregation types.
"""

import random
from .config import METADATA, SPACE_OPERATORS, TIME_INTERVAL_OPERATORS, TIME_DURATION_OPERATORS, CAMERA_OPTIONS, VIDEO_POS2D_OPTIONS, AGGREGATION_COUNT_OPTIONS, AGGREGATION_NUMERIC_OPTIONS, AGGREGATION_SUM_OPTIONS


class QueryPatternGenerator:
    """Handles query pattern generation for different answer types."""
    
    def __init__(self, extractor):
        self.extractor = extractor
    
    def generate_object_pattern(self, selected_answer_type_metadata):
        """Generate query pattern for Object answer type."""
        # Actionをランダムに決める
        query_pattern_Action_type = random.choice(METADATA['Action'])
        query_pattern_Action_value = self.extractor.getActionMetadataValue(query_pattern_Action_type)

        # Sをランダムに決める
        query_pattern_Space_type = random.choice(METADATA['Space'])
        query_pattern_Space_value = self.extractor.getSpaceMetadataValue(query_pattern_Space_type, query_pattern_Action_value)
        if query_pattern_Space_value is None:
            return None

        if query_pattern_Space_type == "Pos3D":
            query_pattern_Space_operator = random.choice(SPACE_OPERATORS)
        else:
            query_pattern_Space_operator = None

        # Tをランダムに決める
        tmp_metadata = METADATA['Time']
        if "Current" in tmp_metadata:
            tmp_metadata.remove("Current")
        query_pattern_Time_type = random.choice(tmp_metadata)
        query_pattern_Time_value = self.extractor.getTimeMetadataValue(query_pattern_Time_type)

        query_pattern_Time_operator = None
        if query_pattern_Time_type == "Interval":
            query_pattern_Time_operator = random.choice(TIME_INTERVAL_OPERATORS)
        elif query_pattern_Time_type == "Duration":
            query_pattern_Time_operator = random.choice(TIME_DURATION_OPERATORS)

        return {
            'query_pattern_Action_type': query_pattern_Action_type,
            'query_pattern_Action_value': query_pattern_Action_value,
            'query_pattern_Space_type': query_pattern_Space_type,
            'query_pattern_Space_value': query_pattern_Space_value,
            'query_pattern_Space_operator': query_pattern_Space_operator,
            'query_pattern_Time_type': query_pattern_Time_type,
            'query_pattern_Time_value': query_pattern_Time_value,
            'query_pattern_Time_operator': query_pattern_Time_operator
        }

    def generate_action_pattern(self, selected_answer_type_metadata):
        """Generate query pattern for Action answer type."""
        # Oをランダムに決める
        query_pattern_Object_type = random.choice(METADATA['Object'])
        query_pattern_Object_value = self.extractor.getObjectMetadataValue(query_pattern_Object_type=query_pattern_Object_type)
        if query_pattern_Object_value is None:
            return None

        # Sをランダムに決める
        query_pattern_Space_type = random.choice(METADATA['Space'])
        query_pattern_Space_value = self.extractor.getSpaceMetadataValue(query_pattern_Space_type, None)
        if query_pattern_Space_type == "Pos3D":
            query_pattern_Space_operator = random.choice(SPACE_OPERATORS)
        else:
            query_pattern_Space_operator = None

        # Tをランダムに決める
        tmp_metadata = METADATA['Time']
        if "Current" in tmp_metadata:
            tmp_metadata.remove("Current")
        query_pattern_Time_type = random.choice(tmp_metadata)
        query_pattern_Time_value = self.extractor.getTimeMetadataValue(query_pattern_Time_type)

        query_pattern_Time_operator = None
        if query_pattern_Time_type == "Interval":
            query_pattern_Time_operator = random.choice(TIME_INTERVAL_OPERATORS)
        elif query_pattern_Time_type == "Duration":
            query_pattern_Time_operator = random.choice(TIME_DURATION_OPERATORS)

        return {
            'query_pattern_Object_type': query_pattern_Object_type,
            'query_pattern_Object_value': query_pattern_Object_value,
            'query_pattern_Space_type': query_pattern_Space_type,
            'query_pattern_Space_value': query_pattern_Space_value,
            'query_pattern_Space_operator': query_pattern_Space_operator,
            'query_pattern_Time_type': query_pattern_Time_type,
            'query_pattern_Time_value': query_pattern_Time_value,
            'query_pattern_Time_operator': query_pattern_Time_operator
        }

    def generate_space_pattern(self, selected_answer_type_metadata):
        """Generate query pattern for Space answer type."""
        # Actionをランダムに決める
        query_pattern_Action_type = random.choice(METADATA['Action'])
        query_pattern_Action_value = self.extractor.getActionMetadataValue(query_pattern_Action_type)

        # Objectをランダムに決める
        query_pattern_Object_type = random.choice(METADATA['Object'])
        query_pattern_Object_value = self.extractor.getObjectMetadataValue(query_pattern_Object_type=query_pattern_Object_type, query_pattern_Action_value=query_pattern_Action_value)
        if query_pattern_Object_value is None:
            return None

        # Timeをランダムに決める
        query_pattern_Time_type = random.choice(METADATA['Time'])
        query_pattern_Time_value = self.extractor.getTimeMetadataValue(query_pattern_Time_type)

        query_pattern_Time_operator = None
        if query_pattern_Time_type == "Interval":
            query_pattern_Time_operator = random.choice(TIME_INTERVAL_OPERATORS)
        elif query_pattern_Time_type == "Duration":
            query_pattern_Time_operator = random.choice(TIME_DURATION_OPERATORS)

        return {
            'query_pattern_Object_type': query_pattern_Object_type,
            'query_pattern_Object_value': query_pattern_Object_value,
            'query_pattern_Action_type': query_pattern_Action_type,
            'query_pattern_Action_value': query_pattern_Action_value,
            'query_pattern_Time_type': query_pattern_Time_type,
            'query_pattern_Time_value': query_pattern_Time_value,
            'query_pattern_Time_operator': query_pattern_Time_operator
        }

    def generate_time_pattern(self, selected_answer_type_metadata):
        """Generate query pattern for Time answer type."""
        # Actionをランダムに決める
        query_pattern_Action_type = random.choice(METADATA['Action'])
        query_pattern_Action_value = self.extractor.getActionMetadataValue(query_pattern_Action_type)

        # Objectをランダムに決める
        query_pattern_Object_type = random.choice(METADATA['Object'])
        query_pattern_Object_value = self.extractor.getObjectMetadataValue(query_pattern_Object_type=query_pattern_Object_type, query_pattern_Action_value=query_pattern_Action_value)
        if query_pattern_Object_value is None:
            return None

        # Spaceをランダムに決める
        query_pattern_Space_type = random.choice(METADATA['Space'])
        query_pattern_Space_value = self.extractor.getSpaceMetadataValue(query_pattern_Space_type, query_pattern_Action_value)
        query_pattern_Space_operator = None
        if query_pattern_Space_type == "Pos3D":
            query_pattern_Space_operator = random.choice(SPACE_OPERATORS)

        return {
            'query_pattern_Object_type': query_pattern_Object_type,
            'query_pattern_Object_value': query_pattern_Object_value,
            'query_pattern_Action_type': query_pattern_Action_type,
            'query_pattern_Action_value': query_pattern_Action_value,
            'query_pattern_Space_type': query_pattern_Space_type,
            'query_pattern_Space_value': query_pattern_Space_value,
            'query_pattern_Space_operator': query_pattern_Space_operator
        }

    def generate_activity_pattern(self, selected_answer_type_metadata):
        """Generate query pattern for Activity answer type."""
        # Actionをランダムに決める
        query_pattern_Action_type = random.choice(METADATA['Action'])
        query_pattern_Action_value = self.extractor.getActionMetadataValue(query_pattern_Action_type)

        # Objectをランダムに決める
        query_pattern_Object_type = random.choice(METADATA['Object'])
        query_pattern_Object_value = self.extractor.getObjectMetadataValue(query_pattern_Object_type=query_pattern_Object_type, query_pattern_Action_value=query_pattern_Action_value)
        if query_pattern_Object_value is None:
            return None

        # Timeをランダムに決める
        tmp_metadata = METADATA['Time']
        if "Current" in tmp_metadata:
            tmp_metadata.remove("Current")
        if "First" in tmp_metadata:
            tmp_metadata.remove("First")
        if "Last" in tmp_metadata:
            tmp_metadata.remove("Last")
        query_pattern_Time_type = random.choice(tmp_metadata)
        query_pattern_Time_value = self.extractor.getTimeMetadataValue(query_pattern_Time_type)

        query_pattern_Time_operator = None
        if query_pattern_Time_type == "Interval":
            query_pattern_Time_operator = random.choice(TIME_INTERVAL_OPERATORS)
        elif query_pattern_Time_type == "Duration":
            query_pattern_Time_operator = random.choice(TIME_DURATION_OPERATORS)

        # Spaceをランダムに決める
        query_pattern_Space_type = random.choice(METADATA['Space'])
        query_pattern_Space_value = self.extractor.getSpaceMetadataValue(query_pattern_Space_type, query_pattern_Action_value)
        query_pattern_Space_operator = None
        if query_pattern_Space_type == "Pos3D":
            query_pattern_Space_operator = random.choice(SPACE_OPERATORS)

        return {
            'query_pattern_Object_type': query_pattern_Object_type,
            'query_pattern_Object_value': query_pattern_Object_value,
            'query_pattern_Action_type': query_pattern_Action_type,
            'query_pattern_Action_value': query_pattern_Action_value,
            'query_pattern_Space_type': query_pattern_Space_type,
            'query_pattern_Space_value': query_pattern_Space_value,
            'query_pattern_Space_operator': query_pattern_Space_operator,
            'query_pattern_Time_type': query_pattern_Time_type,
            'query_pattern_Time_value': query_pattern_Time_value,
            'query_pattern_Time_operator': query_pattern_Time_operator
        }

    def generate_video_pattern(self, selected_answer_type_metadata, selected_answer_type_metadata_value):
        """Generate query pattern for Video answer type."""
        # Actionをランダムに決める
        query_pattern_Action_type = random.choice(METADATA['Action'])
        query_pattern_Action_value = self.extractor.getActionMetadataValue(query_pattern_Action_type)

        # Objectをランダムに決める
        query_pattern_Object_type = random.choice(METADATA['Object'])
        query_pattern_Object_value = self.extractor.getObjectMetadataValue(query_pattern_Object_type=query_pattern_Object_type, query_pattern_Action_value=query_pattern_Action_value)
        if query_pattern_Object_value is None:
            return None

        # Timeをランダムに決める
        query_pattern_Time_type = random.choice(METADATA['Time'])
        query_pattern_Time_value = self.extractor.getTimeMetadataValue(query_pattern_Time_type)

        query_pattern_Time_operator = None
        if query_pattern_Time_type == "Interval":
            query_pattern_Time_operator = random.choice(TIME_INTERVAL_OPERATORS)
        elif query_pattern_Time_type == "Duration":
            query_pattern_Time_operator = random.choice(TIME_DURATION_OPERATORS)

        # Spaceをランダムに決める
        query_pattern_Space_type = random.choice(METADATA['Space'])
        query_pattern_Space_value = self.extractor.getSpaceMetadataValue(query_pattern_Space_type, query_pattern_Action_value)
        query_pattern_Space_operator = None
        if query_pattern_Space_type == "Pos3D":
            query_pattern_Space_operator = random.choice(SPACE_OPERATORS)

        # カメラをランダムに決める
        camera = random.choice(CAMERA_OPTIONS)

        # Videoタイプのメタデータ値の設定
        if selected_answer_type_metadata == "Pos2D":
            # 最初のフレームか最後のフレームかランダムに決める
            selected_answer_type_metadata_value = random.choice(VIDEO_POS2D_OPTIONS)
        else:
            # その他の場合はNoneのまま
            pass

        return {
            'query_pattern_Object_type': query_pattern_Object_type,
            'query_pattern_Object_value': query_pattern_Object_value,
            'query_pattern_Action_type': query_pattern_Action_type,
            'query_pattern_Action_value': query_pattern_Action_value,
            'query_pattern_Space_type': query_pattern_Space_type,
            'query_pattern_Space_value': query_pattern_Space_value,
            'query_pattern_Space_operator': query_pattern_Space_operator,
            'query_pattern_Time_type': query_pattern_Time_type,
            'query_pattern_Time_value': query_pattern_Time_value,
            'query_pattern_Time_operator': query_pattern_Time_operator,
            'camera': camera,
            'selected_answer_type_metadata_value': selected_answer_type_metadata_value
        }

    def generate_aggregation_pattern(self, selected_answer_type_metadata, selected_answer_type_metadata_value):
        """Generate query pattern for Aggregation answer type."""
        # 具体的な集計対象の決定
        if selected_answer_type_metadata == "Count":
            selected_answer_type_metadata_value = random.choice(AGGREGATION_COUNT_OPTIONS)
        elif selected_answer_type_metadata in ["Min", "Max", "Avg"]:
            selected_answer_type_metadata_value = random.choice(AGGREGATION_NUMERIC_OPTIONS)
        elif selected_answer_type_metadata == "Sum":
            selected_answer_type_metadata_value = random.choice(AGGREGATION_SUM_OPTIONS)

        # Actionをランダムに決める
        query_pattern_Action_type = random.choice(METADATA['Action'])
        query_pattern_Action_value = self.extractor.getActionMetadataValue(query_pattern_Action_type)

        # 決定したActionの値を用いて、候補となるObjectの中からランダムに決める
        query_pattern_Object_type = random.choice(METADATA['Object'])
        query_pattern_Object_value = self.extractor.getObjectMetadataValue(query_pattern_Object_type=query_pattern_Object_type, query_pattern_Action_value=query_pattern_Action_value)
        if query_pattern_Object_value is None:
            return None

        # Timeをランダムに決める
        tmp_metadata = METADATA['Time']
        if "Current" in tmp_metadata:
            tmp_metadata.remove("Current")
        if "First" in tmp_metadata:
            tmp_metadata.remove("First")
        if "Last" in tmp_metadata:
            tmp_metadata.remove("Last")
        query_pattern_Time_type = random.choice(tmp_metadata)
        query_pattern_Time_value = self.extractor.getTimeMetadataValue(query_pattern_Time_type)

        query_pattern_Time_operator = None
        if query_pattern_Time_type == "Interval":
            query_pattern_Time_operator = random.choice(TIME_INTERVAL_OPERATORS)
        elif query_pattern_Time_type == "Duration":
            query_pattern_Time_operator = random.choice(TIME_DURATION_OPERATORS)

        # Spaceをランダムに決める
        query_pattern_Space_type = None
        query_pattern_Space_value = None
        query_pattern_Space_operator = None
        if selected_answer_type_metadata_value != "place":
            # 集計対象が場所の場合はSpaceは選択しない
            query_pattern_Space_type = random.choice(METADATA['Space'])
            query_pattern_Space_value = self.extractor.getSpaceMetadataValue(query_pattern_Space_type, query_pattern_Action_value)
            if query_pattern_Space_type == "Pos3D":
                query_pattern_Space_operator = random.choice(SPACE_OPERATORS)

        return {
            'query_pattern_Object_type': query_pattern_Object_type,
            'query_pattern_Object_value': query_pattern_Object_value,
            'query_pattern_Action_type': query_pattern_Action_type,
            'query_pattern_Action_value': query_pattern_Action_value,
            'query_pattern_Space_type': query_pattern_Space_type,
            'query_pattern_Space_value': query_pattern_Space_value,
            'query_pattern_Space_operator': query_pattern_Space_operator,
            'query_pattern_Time_type': query_pattern_Time_type,
            'query_pattern_Time_value': query_pattern_Time_value,
            'query_pattern_Time_operator': query_pattern_Time_operator,
            'selected_answer_type_metadata_value': selected_answer_type_metadata_value
        }

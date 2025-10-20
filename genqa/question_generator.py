#!/usr/bin/env python
# coding: utf-8

"""
Question generation logic.
Handles the main question generation process and dataset creation.
"""

import random
import hashlib
from .config import METADATA, MAX_CHECK_COUNT
from .query_patterns import QueryPatternGenerator


class QuestionGenerator:
    """Handles the main question generation process."""
    
    def __init__(self, extractor):
        self.extractor = extractor
        self.pattern_generator = QueryPatternGenerator(extractor)
    
    def generate_questions(self, loop, selected_answer_type, seen_combinations):
        """Generate questions for the specified answer type."""
        dataset = []
        
        while len(dataset) < loop:
            # Initialize variables
            selected_answer_type_metadata = None
            selected_answer_type_metadata_value = None
            camera = None
            
            print("selected answer type: ", selected_answer_type)
            
            # Select answer type metadata
            selected_answer_type_metadata = self._select_answer_type_metadata(selected_answer_type)
            
            # Generate query pattern
            initial_check_result = False
            check_count = 0
            
            while (initial_check_result != True) and (check_count < MAX_CHECK_COUNT):
                pattern_result = self._generate_query_pattern(
                    selected_answer_type, 
                    selected_answer_type_metadata, 
                    selected_answer_type_metadata_value
                )
                
                if pattern_result is None:
                    print("pattern_result is None - pattern generation failed")
                    check_count += 1
                    continue
                
                # Check if pattern is valid
                initial_check_result, object_query_pattern, action_query_pattern, spatial_query_pattern, temporal_query_pattern = self._check_pattern_validity(
                    selected_answer_type, 
                    pattern_result
                )
                query_patterns = (object_query_pattern, action_query_pattern, spatial_query_pattern, temporal_query_pattern)
                
                if initial_check_result:
                    break
                    
                check_count += 1
            
            if initial_check_result != True:
                print("Failed to generate query pattern after {} attempts".format(MAX_CHECK_COUNT))
                self._print_debug_info(selected_answer_type, selected_answer_type_metadata, 
                                     selected_answer_type_metadata_value, pattern_result)
                continue
            
            # Get metadata value from pattern result
            selected_answer_type_metadata_value = pattern_result.get('selected_answer_type_metadata_value')
            camera = pattern_result.get('camera')
            
            # Generate SPARQL query
            generated_query = self._generate_sparql_query(
                selected_answer_type, 
                selected_answer_type_metadata, 
                selected_answer_type_metadata_value, 
                query_patterns, 
                pattern_result, 
                camera
            )
            
            # Execute SPARQL query
            results = self._execute_sparql_query(generated_query, selected_answer_type_metadata)
            if results is None or len(results) == 0:
                continue
            
            # Generate question text
            text_en, qualifiers_en = self._generate_question_text(
                selected_answer_type, 
                selected_answer_type_metadata, 
                selected_answer_type_metadata_value, 
                pattern_result, 
                camera
            )
            
            # Create combination key for seen_combinations check
            combination_key = self._create_combination_key(
                selected_answer_type, selected_answer_type_metadata, selected_answer_type_metadata_value,
                pattern_result
            )
            
            # Check if this combination has been seen before
            if combination_key in seen_combinations:
                print(f"Combination already seen: {combination_key}")
                continue
            
            # Check for duplication in current dataset
            if self._is_duplicate(dataset, text_en):
                continue
            
            # Add combination to seen_combinations
            seen_combinations.add(combination_key)
            
            # Add to dataset
            dataset.append(self._create_dataset_entry(
                text_en, generated_query, results,
                selected_answer_type, selected_answer_type_metadata, selected_answer_type_metadata_value,
                pattern_result, qualifiers_en
            ))
        
        return dataset, seen_combinations
    
    def _create_combination_key(self, selected_answer_type, selected_answer_type_metadata, selected_answer_type_metadata_value, pattern_result):
        """Create a unique key for the combination of parameters to track seen combinations."""
        # Extract key parameters from pattern_result
        object_type = pattern_result.get('query_pattern_Object_type', 'None')
        object_value = pattern_result.get('query_pattern_Object_value')
        action_type = pattern_result.get('query_pattern_Action_type')
        action_value = pattern_result.get('query_pattern_Action_value')
        space_type = pattern_result.get('query_pattern_Space_type')
        space_value = pattern_result.get('query_pattern_Space_value')
        space_operator = pattern_result.get('query_pattern_Space_operator')
        time_type = pattern_result.get('query_pattern_Time_type')
        time_value = pattern_result.get('query_pattern_Time_value')
        time_operator = pattern_result.get('query_pattern_Time_operator')
        camera = pattern_result.get('camera')
        
        # Create a unique key string
        key_parts = [
            selected_answer_type,
            selected_answer_type_metadata,
            str(selected_answer_type_metadata_value) if selected_answer_type_metadata_value is not None else 'None',
            object_type if object_type is not None else 'None',
            str(object_value) if object_value is not None else 'None',
            action_type if action_type is not None else 'None',
            str(action_value) if action_value is not None else 'None',
            space_type if space_type is not None else 'None',
            str(space_value) if space_value is not None else 'None',
            space_operator if space_operator is not None else 'None',
            time_type if time_type is not None else 'None',
            str(time_value) if time_value is not None else 'None',
            time_operator if time_operator is not None else 'None',
            camera if camera is not None else 'None'
        ]
        
        
        return "|".join(key_parts)
    
    def _select_answer_type_metadata(self, selected_answer_type):
        """Select answer type metadata based on the answer type."""
        if selected_answer_type == "Time" or selected_answer_type == "Space":
            if selected_answer_type == "Time":
                candidate_Time_metadata = ["Instant", "Interval", "Duration"]
                return random.choice(candidate_Time_metadata)
            else:
                candidate_Space_metadata = ["Place", "Pos3D"]  # "Relation" is not supported yet
                return random.choice(candidate_Space_metadata)
        else:
            if selected_answer_type == "Action":
                return "None"  # debug
            else:
                return random.choice(METADATA[selected_answer_type])
    
    def _generate_query_pattern(self, selected_answer_type, selected_answer_type_metadata, selected_answer_type_metadata_value):
        # Generate query pattern based on answer type.
        if selected_answer_type == "Object":
            return self.pattern_generator.generate_object_pattern(selected_answer_type_metadata)
        elif selected_answer_type == "Action":
            return self.pattern_generator.generate_action_pattern(selected_answer_type_metadata)
        elif selected_answer_type == "Space":
            return self.pattern_generator.generate_space_pattern(selected_answer_type_metadata)
        elif selected_answer_type == "Time":
            return self.pattern_generator.generate_time_pattern(selected_answer_type_metadata)
        elif selected_answer_type == "Activity":
            return self.pattern_generator.generate_activity_pattern(selected_answer_type_metadata)
        elif selected_answer_type == "Video":
            return self.pattern_generator.generate_video_pattern(selected_answer_type_metadata, selected_answer_type_metadata_value)
        elif selected_answer_type == "Aggregation":
            return self.pattern_generator.generate_aggregation_pattern(selected_answer_type_metadata, selected_answer_type_metadata_value)
        else:
            return None
    
    def _check_pattern_validity(self, selected_answer_type, pattern_result):
        """Check if the generated pattern is valid."""
        if selected_answer_type == "Object":
            return self.extractor.checkInitialPairs(
                selected_answer_type=selected_answer_type,
                query_pattern_Action_type=pattern_result.get('query_pattern_Action_type'),
                query_pattern_Action_value=pattern_result.get('query_pattern_Action_value'),
                query_pattern_Space_type=pattern_result.get('query_pattern_Space_type'),
                query_pattern_Space_value=pattern_result.get('query_pattern_Space_value'),
                query_pattern_Space_operator=pattern_result.get('query_pattern_Space_operator'),
                query_pattern_Time_type=pattern_result.get('query_pattern_Time_type'),
                query_pattern_Time_value=pattern_result.get('query_pattern_Time_value'),
                query_pattern_Time_operator=pattern_result.get('query_pattern_Time_operator')
            )
        elif selected_answer_type == "Action":
            return self.extractor.checkInitialPairs(
                selected_answer_type=selected_answer_type,
                query_pattern_Object_type=pattern_result.get('query_pattern_Object_type'),
                query_pattern_Object_value=pattern_result.get('query_pattern_Object_value'),
                query_pattern_Space_type=pattern_result.get('query_pattern_Space_type'),
                query_pattern_Space_value=pattern_result.get('query_pattern_Space_value'),
                query_pattern_Space_operator=pattern_result.get('query_pattern_Space_operator'),
                query_pattern_Time_type=pattern_result.get('query_pattern_Time_type'),
                query_pattern_Time_value=pattern_result.get('query_pattern_Time_value'),
                query_pattern_Time_operator=pattern_result.get('query_pattern_Time_operator')
            )
        elif selected_answer_type == "Space":
            return self.extractor.checkInitialPairs(
                selected_answer_type=selected_answer_type,
                query_pattern_Object_type=pattern_result.get('query_pattern_Object_type'),
                query_pattern_Object_value=pattern_result.get('query_pattern_Object_value'),
                query_pattern_Action_type=pattern_result.get('query_pattern_Action_type'),
                query_pattern_Action_value=pattern_result.get('query_pattern_Action_value'),
                query_pattern_Time_type=pattern_result.get('query_pattern_Time_type'),
                query_pattern_Time_value=pattern_result.get('query_pattern_Time_value'),
                query_pattern_Time_operator=pattern_result.get('query_pattern_Time_operator')
            )
        elif selected_answer_type == "Time":
            return self.extractor.checkInitialPairs(
                selected_answer_type=selected_answer_type,
                query_pattern_Object_type=pattern_result.get('query_pattern_Object_type'),
                query_pattern_Object_value=pattern_result.get('query_pattern_Object_value'),
                query_pattern_Action_type=pattern_result.get('query_pattern_Action_type'),
                query_pattern_Action_value=pattern_result.get('query_pattern_Action_value'),
                query_pattern_Space_type=pattern_result.get('query_pattern_Space_type'),
                query_pattern_Space_value=pattern_result.get('query_pattern_Space_value'),
                query_pattern_Space_operator=pattern_result.get('query_pattern_Space_operator')
            )
        elif selected_answer_type == "Activity":
            return self.extractor.checkInitialPairs(
                selected_answer_type=selected_answer_type,
                query_pattern_Object_type=pattern_result.get('query_pattern_Object_type'),
                query_pattern_Object_value=pattern_result.get('query_pattern_Object_value'),
                query_pattern_Action_type=pattern_result.get('query_pattern_Action_type'),
                query_pattern_Action_value=pattern_result.get('query_pattern_Action_value'),
                query_pattern_Space_type=pattern_result.get('query_pattern_Space_type'),
                query_pattern_Space_value=pattern_result.get('query_pattern_Space_value'),
                query_pattern_Space_operator=pattern_result.get('query_pattern_Space_operator'),
                query_pattern_Time_type=pattern_result.get('query_pattern_Time_type'),
                query_pattern_Time_value=pattern_result.get('query_pattern_Time_value'),
                query_pattern_Time_operator=pattern_result.get('query_pattern_Time_operator')
            )
        elif selected_answer_type == "Video":
            return self.extractor.checkInitialPairs(
                selected_answer_type=selected_answer_type,
                query_pattern_Object_type=pattern_result.get('query_pattern_Object_type'),
                query_pattern_Object_value=pattern_result.get('query_pattern_Object_value'),
                query_pattern_Action_type=pattern_result.get('query_pattern_Action_type'),
                query_pattern_Action_value=pattern_result.get('query_pattern_Action_value'),
                query_pattern_Space_type=pattern_result.get('query_pattern_Space_type'),
                query_pattern_Space_value=pattern_result.get('query_pattern_Space_value'),
                query_pattern_Space_operator=pattern_result.get('query_pattern_Space_operator'),
                query_pattern_Time_type=pattern_result.get('query_pattern_Time_type'),
                query_pattern_Time_value=pattern_result.get('query_pattern_Time_value'),
                query_pattern_Time_operator=pattern_result.get('query_pattern_Time_operator')
            )
        elif selected_answer_type == "Aggregation":
            return self.extractor.checkInitialPairs(
                selected_answer_type=selected_answer_type,
                query_pattern_Object_type=pattern_result.get('query_pattern_Object_type'),
                query_pattern_Object_value=pattern_result.get('query_pattern_Object_value'),
                query_pattern_Action_type=pattern_result.get('query_pattern_Action_type'),
                query_pattern_Action_value=pattern_result.get('query_pattern_Action_value'),
                query_pattern_Space_type=pattern_result.get('query_pattern_Space_type'),
                query_pattern_Space_value=pattern_result.get('query_pattern_Space_value'),
                query_pattern_Space_operator=pattern_result.get('query_pattern_Space_operator'),
                query_pattern_Time_type=pattern_result.get('query_pattern_Time_type'),
                query_pattern_Time_value=pattern_result.get('query_pattern_Time_value'),
                query_pattern_Time_operator=pattern_result.get('query_pattern_Time_operator')
            )
        else:
            return False, None
    
    def _generate_sparql_query(self, selected_answer_type, selected_answer_type_metadata, 
                            selected_answer_type_metadata_value, query_patterns, pattern_result, camera):
        """Generate SPARQL query."""
        return self.extractor.generateSPARQL(
            selected_answer_type=selected_answer_type,
            selected_answer_type_metadata=selected_answer_type_metadata,
            selected_answer_type_metadata_value=selected_answer_type_metadata_value,
            object_query_pattern=query_patterns[0] if query_patterns else None,
            action_query_pattern=query_patterns[1] if query_patterns else None,
            spatial_query_pattern=query_patterns[2] if query_patterns else None,
            temporal_query_pattern=query_patterns[3] if query_patterns else None,
            query_pattern_Action_value=pattern_result.get('query_pattern_Action_value'),
            query_pattern_Object_type=pattern_result.get('query_pattern_Object_type'),
            query_pattern_Time_type=pattern_result.get('query_pattern_Time_type'),
            query_pattern_Space_type=pattern_result.get('query_pattern_Space_type'),
            camera=camera
        )
    
    def _execute_sparql_query(self, generated_query, selected_answer_type_metadata):
        """Execute SPARQL query and process results."""
        results = self.extractor.execSPARQL(generated_query)
        if results is None or len(results) == 0:
            return None
        
        if selected_answer_type_metadata == "Video":
            # base64 value is hashed to avoid large output
            print("base64 value is hashed.")
            hashed_results = hashlib.sha256(str(results[0]["answer"]["value"]).encode('utf-8')).hexdigest()
            print("Hashed results:", hashed_results)
            results = [{
                "answer": {
                    "datatype": "http://www.w3.org/2001/XMLSchema#base64Binary",
                    "type": "literal",
                    "value": hashed_results
                }
            }]
        else:
            print(results)
        
        return results
    
    def _generate_question_text(self, selected_answer_type, selected_answer_type_metadata, 
                              selected_answer_type_metadata_value, pattern_result, camera):
        """Generate question text in English."""
        return self.extractor.generateText(
            selected_answer_type=selected_answer_type,
            selected_answer_type_metadata=selected_answer_type_metadata,
            selected_answer_type_metadata_value=selected_answer_type_metadata_value,
            query_pattern_Action_type=pattern_result.get('query_pattern_Action_type'),
            query_pattern_Action_value=pattern_result.get('query_pattern_Action_value'),
            query_pattern_Object_type=pattern_result.get('query_pattern_Object_type'),
            query_pattern_Object_value=pattern_result.get('query_pattern_Object_value'),
            query_pattern_Space_type=pattern_result.get('query_pattern_Space_type'),
            query_pattern_Space_value=pattern_result.get('query_pattern_Space_value'),
            query_pattern_Space_operator=pattern_result.get('query_pattern_Space_operator'),
            query_pattern_Time_type=pattern_result.get('query_pattern_Time_type'),
            query_pattern_Time_value=pattern_result.get('query_pattern_Time_value'),
            query_pattern_Time_operator=pattern_result.get('query_pattern_Time_operator'),
            camera=camera
        )
    
    def _is_duplicate(self, dataset, text_en):
        """Check if the question text is a duplicate."""
        for item in dataset:
            if item["question_text_en"] == text_en:
                return True
        return False
    
    def _create_dataset_entry(self, text_en, generated_query, results,
                            selected_answer_type, selected_answer_type_metadata, selected_answer_type_metadata_value,
                            pattern_result, qualifiers_en):
        """Create a dataset entry."""
        return {
            "question_text_en": text_en,
            "query": generated_query,
            "results": results,
            "selected_answer_type": selected_answer_type,
            "selected_answer_type_metadata": selected_answer_type_metadata,
            "selected_answer_type_metadata_value": selected_answer_type_metadata_value,
            "query_pattern_Object_type": pattern_result.get('query_pattern_Object_type'),
            "query_pattern_Object_value": pattern_result.get('query_pattern_Object_value'),
            "query_pattern_Action_type": pattern_result.get('query_pattern_Action_type'),
            "query_pattern_Action_value": pattern_result.get('query_pattern_Action_value'),
            "query_pattern_Space_type": pattern_result.get('query_pattern_Space_type'),
            "query_pattern_Space_value": pattern_result.get('query_pattern_Space_value'),
            "query_pattern_Time_type": pattern_result.get('query_pattern_Time_type'),
            "query_pattern_Time_value": pattern_result.get('query_pattern_Time_value'),
            "query_pattern_Space_operator": pattern_result.get('query_pattern_Space_operator'),
            "query_pattern_Time_operator": pattern_result.get('query_pattern_Time_operator'),
            "qualifiers_en": qualifiers_en,
        }
    
    def _print_debug_info(self, selected_answer_type, selected_answer_type_metadata, 
                         selected_answer_type_metadata_value, pattern_result):
        """Print debug information when pattern generation fails."""
        print("selected_answer_type", selected_answer_type)
        print("selected_answer_type_metadata", selected_answer_type_metadata)
        print("selected_answer_type_metadata_value", selected_answer_type_metadata_value)
        
        if pattern_result is None:
            print("pattern_result is None - pattern generation failed")
            return
            
        print("query_pattern_Object_type", pattern_result.get('query_pattern_Object_type'))
        print("query_pattern_Object_value", pattern_result.get('query_pattern_Object_value'))
        print("query_pattern_Action_type", pattern_result.get('query_pattern_Action_type'))
        print("query_pattern_Action_value", pattern_result.get('query_pattern_Action_value'))
        print("query_pattern_Space_type", pattern_result.get('query_pattern_Space_type'))
        print("query_pattern_Space_value", pattern_result.get('query_pattern_Space_value'))
        print("query_pattern_Time_type", pattern_result.get('query_pattern_Time_type'))
        print("query_pattern_Time_value", pattern_result.get('query_pattern_Time_value'))
        print("query_pattern_Space_operator", pattern_result.get('query_pattern_Space_operator'))
        print("query_pattern_Time_operator", pattern_result.get('query_pattern_Time_operator'))
        print("Retrying with different answer type or metadata...")
        print("---")

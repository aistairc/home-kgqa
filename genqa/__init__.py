#!/usr/bin/env python
# coding: utf-8

"""
GenQA package for knowledge graph question answering.
Contains modules for question generation, query patterns, and configuration.
"""

# Import configuration first (no dependencies)
from .config import *

# Import other modules only when needed
try:
    from .query_patterns import QueryPatternGenerator
    from .question_generator import QuestionGenerator
except ImportError:
    # Handle missing dependencies gracefully
    pass

try:
    from .extract import *
except ImportError:
    # Handle missing dependencies gracefully
    pass

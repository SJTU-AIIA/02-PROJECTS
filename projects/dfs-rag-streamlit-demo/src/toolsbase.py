from langchain_core.tools import tool
from typing_extensions import List
import numpy as np
import json

@tool(response_format="content")
def mean(query: List):
    """Calculate the mean (average) of a list of numbers."""
    return sum(query) / len(query)

@tool(response_format="content")
def median(query: List[float]):
    """Calculate the median of a list of numbers."""
    return np.median(query)

@tool(response_format="content")
def total_sum(query: List[float]):
    """Calculate the sum of a list of numbers."""
    return np.sum(query)

@tool(response_format="content")
def variance(query: List[float]):
    """Calculate the variance of a list of numbers."""
    return np.var(query)

@tool(response_format="content")
def standard_deviation(query: List[float]):
    """Calculate the standard deviation of a list of numbers."""
    return np.std(query)

@tool(response_format="content")
def data_range(query: List[float]):
    """Calculate the range (difference between max and min) of a list of numbers."""
    return np.ptp(query)  # Peak to peak (max - min)

@tool(response_format="content")
def minimum(query: List[float]):
    """Find the minimum value in a list of numbers."""
    return np.min(query)

@tool(response_format="content")
def maximum(query: List[float]):
    """Find the maximum value in a list of numbers."""
    return np.max(query)

@tool(response_format="content")
def filter_greater_than_or_equal(query: List[float], threshold: float):
    """Filter and return values greater than or equal to a given threshold."""
    return np.array(query)[np.array(query) >= threshold].tolist()

@tool(response_format="content")
def filter_less_than_or_equal(query: List[float], threshold: float):
    """Filter and return values less than or equal to a given threshold."""
    return np.array(query)[np.array(query) <= threshold].tolist()

class MetadataConfig:
    def __init__(self, filename):
        self.filename = filename
        return
    def write(self, metadata):
        with open(self.filename, "w") as f:
            json.dump(metadata, f, indent=4)
    def read(self) -> dict:
        try:
            with open(self.filename, "r") as f:
                metadata = json.load(f)
            return metadata
        except:
            return {}

included_tools = [mean, median, total_sum, variance, standard_deviation, 
                  data_range, minimum, maximum, 
                  filter_greater_than_or_equal, filter_less_than_or_equal]
"""Data handlers with poorly named classes."""
import pandas as pd
from typing import Dict, Any


class DataHandler:
    """Data handler class - should be renamed to DataTransformer."""
    
    def __init__(self):
        self.transform_count = 0
    
    def handle(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle data transformation - should be renamed to transform."""
        # Clean data
        data = self._clean_data(data)
        
        # Apply transformations
        data = self._apply_business_rules(data)
        
        # Normalize data
        data = self._normalize_data(data)
        
        self.transform_count += len(data)
        return data
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean the data."""
        # Remove nulls
        data = data.dropna()
        
        # Remove duplicates
        data = data.drop_duplicates()
        
        return data
    
    def _apply_business_rules(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply business transformation rules."""
        # Convert string columns to proper case
        for col in data.select_dtypes(include=['object']).columns:
            data[col] = data[col].astype(str).str.title()
        
        # Add calculated fields
        if 'price' in data.columns and 'quantity' in data.columns:
            data['total'] = data['price'] * data['quantity']
        
        return data
    
    def _normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize numeric data."""
        numeric_cols = data.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            if col not in ['id', 'quantity']:  # Don't normalize IDs or quantities
                data[col] = (data[col] - data[col].mean()) / data[col].std()
        
        return data


class ValidationHandler:
    """Validation handler that works with DataHandler."""
    
    def __init__(self):
        self.data_handler = DataHandler()  # Reference needs updating
    
    def validate_and_handle(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate data and then handle it."""
        # Basic validation
        if data.empty:
            raise ValueError("Empty dataset provided")
        
        # Use handler to process
        return self.data_handler.handle(data)  # Method call needs updating

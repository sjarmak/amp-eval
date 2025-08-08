"""Data processor with poorly named classes."""
import pandas as pd
from typing import List, Dict, Any
from .handlers import DataHandler


class DataProcessor:
    """Main data processor class - should be renamed to ETLPipeline."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.handler = DataHandler()  # Reference that needs updating
        self.processed_count = 0
    
    def process(self, data: List[Dict]) -> pd.DataFrame:
        """Process data - should be renamed to run_pipeline."""
        print(f"Processing {len(data)} records...")
        
        # Extract phase
        extracted_data = self._extract(data)
        
        # Transform phase using handler
        transformed_data = self.handler.handle(extracted_data)  # Method name needs updating
        
        # Load phase
        result = self._load(transformed_data)
        
        self.processed_count += len(data)
        return result
    
    def _extract(self, data: List[Dict]) -> pd.DataFrame:
        """Extract phase of ETL."""
        return pd.DataFrame(data)
    
    def _load(self, data: pd.DataFrame) -> pd.DataFrame:
        """Load phase of ETL."""
        # Apply final transformations
        data['processed_at'] = pd.Timestamp.now()
        return data
    
    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        return {
            'total_processed': self.processed_count,
            'handler_transforms': self.handler.transform_count  # Property name may need updating
        }


class BatchProcessor:
    """Batch processor that uses DataProcessor."""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.processor = DataProcessor({})  # Reference needs updating
    
    def process_batches(self, data: List[Dict]) -> List[pd.DataFrame]:
        """Process data in batches."""
        results = []
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            result = self.processor.process(batch)  # Method call needs updating
            results.append(result)
        return results

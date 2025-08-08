"""Pipeline runner that uses the processor classes."""
import json
from typing import List, Dict
from .processor import DataProcessor, BatchProcessor  # Imports need updating
from .handlers import DataHandler  # Import needs updating


class PipelineRunner:
    """Main pipeline runner."""
    
    def __init__(self, config_file: str):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # Create processor instance
        self.processor = DataProcessor(self.config)  # Class name needs updating
        self.batch_processor = BatchProcessor(batch_size=self.config.get('batch_size', 100))
        
        # Create handler for validation
        self.validator_handler = DataHandler()  # Class name needs updating
    
    def run_single_batch(self, data: List[Dict]) -> None:
        """Run single batch processing."""
        print("Starting single batch processing...")
        result = self.processor.process(data)  # Method name needs updating
        print(f"Processed {len(result)} records")
        
        # Get stats
        stats = self.processor.get_stats()
        print(f"Processing stats: {stats}")
    
    def run_batch_processing(self, data: List[Dict]) -> None:
        """Run batch processing."""
        print("Starting batch processing...")
        results = self.batch_processor.process_batches(data)
        print(f"Processed {len(results)} batches")
    
    def validate_data(self, data: List[Dict]) -> bool:
        """Validate data using handler."""
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            self.validator_handler.handle(df)  # Method name needs updating
            return True
        except Exception as e:
            print(f"Validation failed: {e}")
            return False


def main():
    """Main function demonstrating usage."""
    # Sample data
    sample_data = [
        {'id': 1, 'name': 'john doe', 'price': 10.0, 'quantity': 2},
        {'id': 2, 'name': 'jane smith', 'price': 15.0, 'quantity': 1},
        {'id': 3, 'name': 'bob johnson', 'price': 8.0, 'quantity': 3}
    ]
    
    # Create config file
    config = {'batch_size': 50, 'normalize': True}
    with open('config.json', 'w') as f:
        json.dump(config, f)
    
    # Run pipeline
    runner = PipelineRunner('config.json')
    
    if runner.validate_data(sample_data):
        runner.run_single_batch(sample_data)
        runner.run_batch_processing(sample_data)


if __name__ == "__main__":
    main()

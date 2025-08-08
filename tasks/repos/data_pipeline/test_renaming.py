"""Tests to validate class and method renaming."""
import pytest
import pandas as pd
import json
import os


def test_etl_pipeline_class_exists():
    """Test that DataProcessor has been renamed to ETLPipeline."""
    try:
        from processor import ETLPipeline
        assert ETLPipeline is not None
    except ImportError:
        pytest.fail("ETLPipeline class not found - DataProcessor should be renamed")


def test_data_transformer_class_exists():
    """Test that DataHandler has been renamed to DataTransformer."""
    try:
        from handlers import DataTransformer
        assert DataTransformer is not None
    except ImportError:
        pytest.fail("DataTransformer class not found - DataHandler should be renamed")


def test_run_pipeline_method_exists():
    """Test that process() method has been renamed to run_pipeline()."""
    try:
        from processor import ETLPipeline
        pipeline = ETLPipeline({})
        assert hasattr(pipeline, 'run_pipeline')
        assert not hasattr(pipeline, 'process')
    except (ImportError, AttributeError):
        pytest.fail("run_pipeline method not found - process() should be renamed")


def test_transform_method_exists():
    """Test that handle() method has been renamed to transform()."""
    try:
        from handlers import DataTransformer
        transformer = DataTransformer()
        assert hasattr(transformer, 'transform')
        assert not hasattr(transformer, 'handle')
    except (ImportError, AttributeError):
        pytest.fail("transform method not found - handle() should be renamed")


def test_imports_updated():
    """Test that all imports have been updated."""
    # Check pipeline_runner imports
    with open('pipeline_runner.py', 'r') as f:
        content = f.read()
        # Should import ETLPipeline, not DataProcessor
        assert 'ETLPipeline' in content
        assert 'DataTransformer' in content


def test_method_calls_updated():
    """Test that all method calls have been updated."""
    with open('pipeline_runner.py', 'r') as f:
        content = f.read()
        # Should call run_pipeline, not process
        assert 'run_pipeline' in content
        assert 'transform' in content


def test_functionality_preserved():
    """Test that functionality is preserved after renaming."""
    # Create test data
    test_data = [
        {'id': 1, 'name': 'test', 'price': 10.0, 'quantity': 2}
    ]
    
    try:
        from processor import ETLPipeline
        from handlers import DataTransformer
        
        # Test that basic functionality still works
        pipeline = ETLPipeline({})
        result = pipeline.run_pipeline(test_data)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        
        # Test transformer
        transformer = DataTransformer()
        df = pd.DataFrame(test_data)
        transformed = transformer.transform(df)
        
        assert isinstance(transformed, pd.DataFrame)
        
    except ImportError:
        pytest.fail("Renamed classes/methods should maintain functionality")


def test_cross_references_updated():
    """Test that cross-references between files are updated."""
    try:
        from processor import BatchProcessor
        batch_proc = BatchProcessor()
        
        # Should have reference to ETLPipeline, not DataProcessor
        assert hasattr(batch_proc, 'processor')
        assert batch_proc.processor.__class__.__name__ == 'ETLPipeline'
        
    except (ImportError, AttributeError):
        pytest.fail("Cross-references not properly updated")


if __name__ == "__main__":
    pytest.main([__file__])

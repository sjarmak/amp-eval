#!/usr/bin/env python3
"""
Plugin loader for custom graders.
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base import BaseGrader, GraderConfig, GraderFactory, GraderType


class GraderPluginLoader:
    """Loads custom grader plugins from evaluation directories."""
    
    def __init__(self):
        self._loaded_plugins = {}
    
    def load_grader_for_evaluation(self, eval_yaml_path: str) -> Optional[BaseGrader]:
        """Load custom grader plugin located next to evaluation YAML."""
        eval_path = Path(eval_yaml_path)
        grader_file = eval_path.parent / "grader.py"
        
        if not grader_file.exists():
            return None
        
        # Check if already loaded
        grader_module_name = f"grader_{eval_path.stem}"
        if grader_module_name in self._loaded_plugins:
            return self._loaded_plugins[grader_module_name]
        
        try:
            # Load the grader module
            spec = importlib.util.spec_from_file_location(grader_module_name, grader_file)
            if spec is None or spec.loader is None:
                print(f"Failed to load grader spec from {grader_file}")
                return None
            
            grader_module = importlib.util.module_from_spec(spec)
            sys.modules[grader_module_name] = grader_module
            spec.loader.exec_module(grader_module)
            
            # Look for grader classes in the module
            grader_instance = self._extract_grader_from_module(grader_module, eval_path.stem)
            
            if grader_instance:
                self._loaded_plugins[grader_module_name] = grader_instance
                return grader_instance
            else:
                print(f"No valid grader found in {grader_file}")
                return None
                
        except Exception as e:
            print(f"Failed to load grader plugin {grader_file}: {e}")
            return None
    
    def _extract_grader_from_module(self, module, eval_name: str) -> Optional[BaseGrader]:
        """Extract grader instance from loaded module."""
        # Look for a create_grader function (preferred)
        if hasattr(module, 'create_grader'):
            try:
                return module.create_grader()
            except Exception as e:
                print(f"Failed to call create_grader() in {eval_name}: {e}")
        
        # Look for a grader instance variable
        for attr_name in ['grader', 'GRADER', 'custom_grader']:
            if hasattr(module, attr_name):
                grader = getattr(module, attr_name)
                if isinstance(grader, BaseGrader):
                    return grader
        
        # Look for grader classes and instantiate
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, BaseGrader) and 
                attr != BaseGrader):
                try:
                    # Try to instantiate with default config
                    config = GraderConfig(
                        name=f"custom_{eval_name}",
                        grader_type=GraderType.CUSTOM
                    )
                    return attr(config)
                except Exception as e:
                    print(f"Failed to instantiate grader class {attr_name}: {e}")
        
        return None
    
    def load_all_plugins(self, eval_directory: str) -> Dict[str, BaseGrader]:
        """Load all grader plugins from an evaluation directory."""
        eval_dir = Path(eval_directory)
        loaded_graders = {}
        
        for yaml_file in eval_dir.glob("*.yaml"):
            grader = self.load_grader_for_evaluation(str(yaml_file))
            if grader:
                loaded_graders[yaml_file.stem] = grader
        
        return loaded_graders
    
    def register_plugin_grader(self, name: str, grader_class: type):
        """Register a custom grader class."""
        GraderFactory.register_grader(GraderType.CUSTOM, grader_class)
        print(f"Registered custom grader: {name}")
    
    def get_loaded_plugins(self) -> Dict[str, BaseGrader]:
        """Get all currently loaded plugins."""
        return self._loaded_plugins.copy()
    
    def clear_plugins(self):
        """Clear all loaded plugins."""
        # Remove from sys.modules
        for module_name in list(self._loaded_plugins.keys()):
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        self._loaded_plugins.clear()


# Example custom grader template
GRADER_TEMPLATE = '''#!/usr/bin/env python3
"""
Custom grader for {eval_name} evaluation.
Place this file as grader.py next to your evaluation YAML.
"""

from amp_eval.graders.base import BaseGrader, GraderConfig, GradeResult, GraderType
from typing import Dict, Any


class Custom{eval_name_title}Grader(BaseGrader):
    """Custom grader for {eval_name} evaluation."""
    
    def __init__(self, config: GraderConfig):
        super().__init__(config)
    
    def grade(self, response: str, expected: Any = None, context: Dict[str, Any] = None) -> GradeResult:
        """Grade the response using custom logic."""
        # TODO: Implement your custom grading logic here
        
        # Example: Check if response contains certain keywords
        keywords = ["function", "class", "import"]
        found_keywords = sum(1 for keyword in keywords if keyword in response.lower())
        
        score = found_keywords / len(keywords)
        passed = score >= self.config.pass_threshold
        
        return GradeResult(
            score=score,
            max_score=1.0,
            passed=passed,
            feedback=f"Found {{found_keywords}}/{{len(keywords)}} keywords",
            details={{"keywords_found": found_keywords, "total_keywords": len(keywords)}}
        )
    
    def get_grader_info(self) -> Dict[str, Any]:
        return {{
            "type": "custom",
            "description": "Custom grader for {eval_name}",
            "parameters": []
        }}


def create_grader() -> BaseGrader:
    """Factory function to create the grader instance."""
    config = GraderConfig(
        name="custom_{eval_name}",
        grader_type=GraderType.CUSTOM,
        pass_threshold=0.7
    )
    return Custom{eval_name_title}Grader(config)
'''


def create_grader_template(eval_name: str, output_path: str):
    """Create a grader template file for a specific evaluation."""
    eval_name_clean = eval_name.replace("-", "_").replace(" ", "_")
    eval_name_title = "".join(word.capitalize() for word in eval_name_clean.split("_"))
    
    content = GRADER_TEMPLATE.format(
        eval_name=eval_name_clean,
        eval_name_title=eval_name_title
    )
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Created grader template: {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Grader plugin utilities")
    parser.add_argument("--create-template", help="Create grader template for evaluation")
    parser.add_argument("--output", help="Output path for template")
    
    args = parser.parse_args()
    
    if args.create_template:
        output_path = args.output or f"grader_{args.create_template}.py"
        create_grader_template(args.create_template, output_path)

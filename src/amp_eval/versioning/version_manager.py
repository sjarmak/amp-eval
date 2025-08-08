#!/usr/bin/env python3
"""
Evaluation suite versioning and compatibility management.
"""

import os
import json
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import semantic_version


class VersionStrategy(Enum):
    """Version compatibility strategies."""
    STRICT = "strict"  # Exact version match required
    COMPATIBLE = "compatible"  # Semantic version compatibility
    LATEST = "latest"  # Always use latest available


@dataclass
class EvaluationVersion:
    """Version information for an evaluation suite."""
    name: str
    version: str
    description: str
    created: str
    author: str
    schema_version: str = "1.0"
    dependencies: Dict[str, str] = None
    breaking_changes: List[str] = None
    checksum: str = ""
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = {}
        if self.breaking_changes is None:
            self.breaking_changes = []


@dataclass
class VersionCompatibility:
    """Compatibility information between versions."""
    from_version: str
    to_version: str
    compatible: bool
    migration_required: bool
    migration_notes: str = ""
    breaking_changes: List[str] = None
    
    def __post_init__(self):
        if self.breaking_changes is None:
            self.breaking_changes = []


class VersionManager:
    """Manages versioning for evaluation suites."""
    
    def __init__(self, base_directory: str = "evals", versions_directory: str = "versions"):
        self.base_dir = Path(base_directory)
        self.versions_dir = Path(versions_directory)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        
        # Version registry file
        self.registry_file = self.versions_dir / "registry.json"
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load the version registry."""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {"evaluations": {}, "schema_version": "1.0"}
    
    def _save_registry(self):
        """Save the version registry."""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def create_version(self, eval_name: str, version: str, description: str, 
                      author: str = "Unknown") -> EvaluationVersion:
        """Create a new version of an evaluation suite."""
        eval_file = self.base_dir / f"{eval_name}.yaml"
        if not eval_file.exists():
            raise FileNotFoundError(f"Evaluation file not found: {eval_file}")
        
        # Calculate checksum
        checksum = self._calculate_checksum(eval_file)
        
        # Create version info
        eval_version = EvaluationVersion(
            name=eval_name,
            version=version,
            description=description,
            created=datetime.now().isoformat(),
            author=author,
            checksum=checksum
        )
        
        # Store version
        self._store_version(eval_version, eval_file)
        
        # Update registry
        if eval_name not in self.registry["evaluations"]:
            self.registry["evaluations"][eval_name] = {"versions": []}
        
        self.registry["evaluations"][eval_name]["versions"].append({
            "version": version,
            "created": eval_version.created,
            "author": author,
            "checksum": checksum
        })
        
        self._save_registry()
        
        print(f"Created version {version} for evaluation {eval_name}")
        return eval_version
    
    def _store_version(self, eval_version: EvaluationVersion, eval_file: Path):
        """Store a versioned evaluation file."""
        # Create version directory
        version_dir = self.versions_dir / eval_version.name / eval_version.version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy evaluation file
        eval_copy = version_dir / f"{eval_version.name}.yaml"
        with open(eval_file, 'r') as src, open(eval_copy, 'w') as dst:
            dst.write(src.read())
        
        # Store version metadata
        metadata_file = version_dir / "version.json"
        with open(metadata_file, 'w') as f:
            json.dump(asdict(eval_version), f, indent=2)
        
        # Copy any associated files (grader.py, etc.)
        grader_file = eval_file.parent / "grader.py"
        if grader_file.exists():
            grader_copy = version_dir / "grader.py"
            with open(grader_file, 'r') as src, open(grader_copy, 'w') as dst:
                dst.write(src.read())
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def get_version(self, eval_name: str, version: str) -> Optional[EvaluationVersion]:
        """Get a specific version of an evaluation."""
        version_dir = self.versions_dir / eval_name / version
        metadata_file = version_dir / "version.json"
        
        if not metadata_file.exists():
            return None
        
        with open(metadata_file, 'r') as f:
            data = json.load(f)
        
        return EvaluationVersion(**data)
    
    def list_versions(self, eval_name: str) -> List[str]:
        """List all versions of an evaluation."""
        if eval_name not in self.registry["evaluations"]:
            return []
        
        versions = self.registry["evaluations"][eval_name]["versions"]
        return [v["version"] for v in versions]
    
    def get_latest_version(self, eval_name: str) -> Optional[str]:
        """Get the latest version of an evaluation."""
        versions = self.list_versions(eval_name)
        if not versions:
            return None
        
        # Sort by semantic version
        try:
            semantic_versions = [semantic_version.Version(v) for v in versions]
            latest = max(semantic_versions)
            return str(latest)
        except ValueError:
            # Fallback to chronological sorting
            eval_versions = self.registry["evaluations"][eval_name]["versions"]
            latest = max(eval_versions, key=lambda x: x["created"])
            return latest["version"]
    
    def check_compatibility(self, eval_name: str, from_version: str, 
                          to_version: str) -> VersionCompatibility:
        """Check compatibility between two versions."""
        try:
            from_sem = semantic_version.Version(from_version)
            to_sem = semantic_version.Version(to_version)
            
            # Major version change = breaking
            if from_sem.major != to_sem.major:
                return VersionCompatibility(
                    from_version=from_version,
                    to_version=to_version,
                    compatible=False,
                    migration_required=True,
                    migration_notes="Major version change detected",
                    breaking_changes=["Major version incompatibility"]
                )
            
            # Minor version change = compatible but may need migration
            if from_sem.minor != to_sem.minor:
                return VersionCompatibility(
                    from_version=from_version,
                    to_version=to_version,
                    compatible=True,
                    migration_required=to_sem.minor > from_sem.minor,
                    migration_notes="Minor version change - check for new features"
                )
            
            # Patch version change = fully compatible
            return VersionCompatibility(
                from_version=from_version,
                to_version=to_version,
                compatible=True,
                migration_required=False,
                migration_notes="Patch version - fully compatible"
            )
            
        except ValueError:
            # Non-semantic versions - assume incompatible
            return VersionCompatibility(
                from_version=from_version,
                to_version=to_version,
                compatible=False,
                migration_required=True,
                migration_notes="Non-semantic versions - compatibility unknown"
            )
    
    def resolve_version(self, eval_name: str, version_spec: str, 
                       strategy: VersionStrategy = VersionStrategy.COMPATIBLE) -> Optional[str]:
        """Resolve a version specification to an actual version."""
        available_versions = self.list_versions(eval_name)
        if not available_versions:
            return None
        
        if version_spec == "latest":
            return self.get_latest_version(eval_name)
        
        if strategy == VersionStrategy.STRICT:
            return version_spec if version_spec in available_versions else None
        
        if strategy == VersionStrategy.LATEST:
            return self.get_latest_version(eval_name)
        
        if strategy == VersionStrategy.COMPATIBLE:
            try:
                target_version = semantic_version.Version(version_spec)
                compatible_versions = []
                
                for v in available_versions:
                    try:
                        candidate = semantic_version.Version(v)
                        # Compatible if same major version and >= minor.patch
                        if (candidate.major == target_version.major and 
                            candidate >= target_version):
                            compatible_versions.append(candidate)
                    except ValueError:
                        continue
                
                if compatible_versions:
                    latest_compatible = max(compatible_versions)
                    return str(latest_compatible)
                
                # Fallback to exact match
                return version_spec if version_spec in available_versions else None
                
            except ValueError:
                # Non-semantic version - fallback to exact match
                return version_spec if version_spec in available_versions else None
        
        return None
    
    def load_versioned_evaluation(self, eval_name: str, version: str) -> Tuple[Dict[str, Any], str]:
        """Load a specific version of an evaluation."""
        resolved_version = self.resolve_version(eval_name, version)
        if not resolved_version:
            raise ValueError(f"Cannot resolve version {version} for evaluation {eval_name}")
        
        version_dir = self.versions_dir / eval_name / resolved_version
        eval_file = version_dir / f"{eval_name}.yaml"
        
        if not eval_file.exists():
            raise FileNotFoundError(f"Versioned evaluation file not found: {eval_file}")
        
        with open(eval_file, 'r') as f:
            eval_data = yaml.safe_load(f)
        
        return eval_data, resolved_version
    
    def migrate_evaluation(self, eval_name: str, from_version: str, 
                          to_version: str) -> Dict[str, Any]:
        """Migrate an evaluation from one version to another."""
        compatibility = self.check_compatibility(eval_name, from_version, to_version)
        
        if not compatibility.compatible:
            raise ValueError(f"Cannot migrate from {from_version} to {to_version}: incompatible versions")
        
        # Load source version
        source_data, _ = self.load_versioned_evaluation(eval_name, from_version)
        
        # Apply migration if needed
        if compatibility.migration_required:
            migrated_data = self._apply_migration(source_data, from_version, to_version)
        else:
            migrated_data = source_data
        
        return {
            "migrated_data": migrated_data,
            "migration_notes": compatibility.migration_notes,
            "breaking_changes": compatibility.breaking_changes
        }
    
    def _apply_migration(self, data: Dict[str, Any], from_version: str, 
                        to_version: str) -> Dict[str, Any]:
        """Apply version migration transformations."""
        # This is a simplified migration framework
        # In practice, you'd have specific migration rules for each version pair
        
        migrated = data.copy()
        
        # Example migration rules
        try:
            from_sem = semantic_version.Version(from_version)
            to_sem = semantic_version.Version(to_version)
            
            # Version 1.x to 2.x migrations
            if from_sem.major == 1 and to_sem.major == 2:
                # Example: rename 'tests' to 'tasks'
                if 'tests' in migrated:
                    migrated['tasks'] = migrated.pop('tests')
                
                # Example: update grading format
                if 'grading' in migrated:
                    old_grading = migrated['grading']
                    migrated['grading'] = {
                        'type': old_grading.get('method', 'exact_match'),
                        'pass_threshold': old_grading.get('threshold', 0.7)
                    }
            
            # Add version info
            migrated['version'] = to_version
            migrated['migrated_from'] = from_version
            migrated['migration_timestamp'] = datetime.now().isoformat()
            
        except ValueError:
            # Non-semantic versions - basic migration
            migrated['version'] = to_version
            migrated['migrated_from'] = from_version
        
        return migrated
    
    def validate_version_format(self, version: str) -> bool:
        """Validate version string format."""
        try:
            semantic_version.Version(version)
            return True
        except ValueError:
            # Allow some non-semantic formats
            import re
            # Allow formats like v1.0, 1.0.0-beta, etc.
            pattern = r'^v?(\d+)\.(\d+)(?:\.(\d+))?(?:-([a-zA-Z0-9.-]+))?$'
            return bool(re.match(pattern, version))
    
    def create_version_tag(self, eval_name: str, version: str, 
                          tag_name: str, description: str = ""):
        """Create a named tag for a version."""
        if eval_name not in self.registry["evaluations"]:
            raise ValueError(f"Evaluation {eval_name} not found")
        
        if "tags" not in self.registry["evaluations"][eval_name]:
            self.registry["evaluations"][eval_name]["tags"] = {}
        
        self.registry["evaluations"][eval_name]["tags"][tag_name] = {
            "version": version,
            "description": description,
            "created": datetime.now().isoformat()
        }
        
        self._save_registry()
        print(f"Created tag '{tag_name}' for {eval_name} v{version}")
    
    def get_version_by_tag(self, eval_name: str, tag_name: str) -> Optional[str]:
        """Get version by tag name."""
        if eval_name not in self.registry["evaluations"]:
            return None
        
        tags = self.registry["evaluations"][eval_name].get("tags", {})
        if tag_name in tags:
            return tags[tag_name]["version"]
        
        return None
    
    def export_version(self, eval_name: str, version: str, export_path: str):
        """Export a specific version to a standalone file."""
        eval_data, resolved_version = self.load_versioned_evaluation(eval_name, version)
        version_info = self.get_version(eval_name, resolved_version)
        
        export_package = {
            "evaluation": eval_data,
            "version_info": asdict(version_info),
            "exported_at": datetime.now().isoformat()
        }
        
        with open(export_path, 'w') as f:
            json.dump(export_package, f, indent=2)
        
        print(f"Exported {eval_name} v{resolved_version} to {export_path}")
    
    def import_version(self, import_path: str) -> EvaluationVersion:
        """Import a version from an exported file."""
        with open(import_path, 'r') as f:
            package = json.load(f)
        
        version_info = EvaluationVersion(**package["version_info"])
        eval_data = package["evaluation"]
        
        # Create temporary file for the evaluation
        temp_file = Path(f"/tmp/{version_info.name}.yaml")
        with open(temp_file, 'w') as f:
            yaml.dump(eval_data, f)
        
        # Store the version
        self._store_version(version_info, temp_file)
        
        # Update registry
        if version_info.name not in self.registry["evaluations"]:
            self.registry["evaluations"][version_info.name] = {"versions": []}
        
        self.registry["evaluations"][version_info.name]["versions"].append({
            "version": version_info.version,
            "created": version_info.created,
            "author": version_info.author,
            "checksum": version_info.checksum
        })
        
        self._save_registry()
        
        # Clean up temp file
        temp_file.unlink()
        
        print(f"Imported {version_info.name} v{version_info.version}")
        return version_info


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluation versioning utilities")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create version
    create_parser = subparsers.add_parser("create", help="Create new version")
    create_parser.add_argument("eval_name", help="Evaluation name")
    create_parser.add_argument("version", help="Version string")
    create_parser.add_argument("--description", required=True, help="Version description")
    create_parser.add_argument("--author", default="Unknown", help="Author name")
    
    # List versions
    list_parser = subparsers.add_parser("list", help="List versions")
    list_parser.add_argument("eval_name", help="Evaluation name")
    
    # Check compatibility
    compat_parser = subparsers.add_parser("compatibility", help="Check version compatibility")
    compat_parser.add_argument("eval_name", help="Evaluation name")
    compat_parser.add_argument("from_version", help="From version")
    compat_parser.add_argument("to_version", help="To version")
    
    # Export version
    export_parser = subparsers.add_parser("export", help="Export version")
    export_parser.add_argument("eval_name", help="Evaluation name")
    export_parser.add_argument("version", help="Version to export")
    export_parser.add_argument("output", help="Output file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        exit(1)
    
    manager = VersionManager()
    
    if args.command == "create":
        version = manager.create_version(args.eval_name, args.version, 
                                       args.description, args.author)
        print(f"Created version: {asdict(version)}")
    
    elif args.command == "list":
        versions = manager.list_versions(args.eval_name)
        print(f"Versions for {args.eval_name}:")
        for v in versions:
            print(f"  - {v}")
    
    elif args.command == "compatibility":
        compat = manager.check_compatibility(args.eval_name, args.from_version, args.to_version)
        print(f"Compatibility: {asdict(compat)}")
    
    elif args.command == "export":
        manager.export_version(args.eval_name, args.version, args.output)

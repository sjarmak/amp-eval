#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Legacy Python code that needs migration to modern standards
Issues: Python 2 style, poor error handling, no type hints, deprecated libraries
"""

import sys
import os
import json
import logging
import urllib2  # Python 2 library - needs updating
import urlparse  # Python 2 library - needs updating
from StringIO import StringIO  # Python 2 library - needs updating
import ConfigParser  # Python 2 library - needs updating
import cPickle as pickle  # Python 2 library - needs updating

# Old-style logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegacyDataProcessor:
    """Legacy data processor with Python 2 patterns that need updating."""
    
    def __init__(self, config_file):
        # Old-style string handling
        self.config_file = config_file
        self.config = self._load_config()
        self.cache = {}
        
        # Python 2 style exception handling
        try:
            self.api_key = self.config.get('api', 'key')
        except ConfigParser.NoSectionError, e:  # Python 2 syntax
            print "Error loading config: %s" % e  # Python 2 print statement
            sys.exit(1)
    
    def _load_config(self):
        """Load configuration using old ConfigParser."""
        config = ConfigParser.ConfigParser()  # Old-style class
        
        # Python 2 style file handling
        try:
            config.read(self.config_file)
        except IOError, e:  # Python 2 exception syntax
            print "Cannot read config file: %s" % e
            raise
        
        return config
    
    def fetch_data(self, url, params=None):
        """Fetch data using legacy urllib2."""
        # Build URL with parameters (Python 2 way)
        if params:
            query_string = '&'.join(['%s=%s' % (k, v) for k, v in params.iteritems()])  # Python 2 iteritems()
            url = '%s?%s' % (url, query_string)
        
        # Old-style URL handling
        parsed_url = urlparse.urlparse(url)
        
        # Legacy HTTP request
        request = urllib2.Request(url)
        request.add_header('API-Key', self.api_key)
        request.add_header('User-Agent', 'LegacyProcessor/1.0')
        
        try:
            response = urllib2.urlopen(request, timeout=30)
            data = response.read()
            return data
        except urllib2.HTTPError, e:  # Python 2 exception syntax
            logger.error("HTTP Error: %s" % e.code)
            return None
        except urllib2.URLError, e:  # Python 2 exception syntax
            logger.error("URL Error: %s" % e.reason)
            return None
    
    def process_json_data(self, json_data):
        """Process JSON data with old-style patterns."""
        try:
            # Python 2 style JSON handling
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            # Old-style iteration
            results = []
            for item in data:
                if item.has_key('status') and item['status'] == 'active':  # Python 2 has_key()
                    processed_item = self._process_item(item)
                    results.append(processed_item)
            
            return results
            
        except ValueError, e:  # Python 2 exception syntax
            print "JSON parsing error: %s" % e
            return []
    
    def _process_item(self, item):
        """Process individual item with legacy patterns."""
        # Old-style string formatting
        processed = {
            'id': item.get('id', 0),
            'name': unicode(item.get('name', '')),  # Python 2 unicode()
            'description': unicode(item.get('description', '')),
            'score': float(item.get('score', 0.0)),
            'tags': [unicode(tag) for tag in item.get('tags', [])],
        }
        
        # Legacy data transformation
        if processed['score'] > 0:
            processed['category'] = 'high'
        else:
            processed['category'] = 'low'
        
        return processed
    
    def save_to_cache(self, key, data):
        """Save data to cache using pickle."""
        # Python 2 style file operations
        cache_file = '/tmp/cache_%s.pkl' % key.replace('/', '_')
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f, protocol=2)  # Python 2 pickle protocol
            print "Data cached to: %s" % cache_file
        except IOError, e:
            print "Cache write error: %s" % e
    
    def load_from_cache(self, key):
        """Load data from cache."""
        cache_file = '/tmp/cache_%s.pkl' % key.replace('/', '_')
        
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            return data
        except (IOError, EOFError), e:  # Python 2 multiple exception syntax
            print "Cache read error: %s" % e
            return None
    
    def export_to_csv(self, data, filename):
        """Export data to CSV with old-style methods."""
        import csv
        
        # Python 2 style CSV writing
        with open(filename, 'wb') as csvfile:  # Python 2 binary mode for CSV
            if data:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Python 2 doesn't have writeheader()
                header = dict((fn, fn) for fn in fieldnames)
                writer.writerow(header)
                
                for row in data:
                    # Convert unicode to UTF-8 for CSV
                    encoded_row = {}
                    for k, v in row.iteritems():  # Python 2 iteritems()
                        if isinstance(v, unicode):
                            encoded_row[k] = v.encode('utf-8')
                        else:
                            encoded_row[k] = v
                    writer.writerow(encoded_row)
        
        print "Data exported to: %s" % filename
    
    def batch_process(self, urls):
        """Process multiple URLs sequentially (inefficient)."""
        results = []
        
        for i, url in enumerate(urls):
            print "Processing %d/%d: %s" % (i + 1, len(urls), url)
            
            # Check cache first
            cache_key = url.split('/')[-1]
            cached_data = self.load_from_cache(cache_key)
            
            if cached_data:
                print "Using cached data for: %s" % url
                results.extend(cached_data)
                continue
            
            # Fetch and process data
            raw_data = self.fetch_data(url)
            if raw_data:
                processed_data = self.process_json_data(raw_data)
                results.extend(processed_data)
                
                # Cache the results
                self.save_to_cache(cache_key, processed_data)
            
            # Old-style progress indication
            if (i + 1) % 10 == 0:
                print "Processed %d URLs..." % (i + 1)
        
        return results


def create_config_file():
    """Create a sample config file with old-style methods."""
    config = ConfigParser.ConfigParser()
    
    config.add_section('api')
    config.set('api', 'key', 'your-api-key-here')
    config.set('api', 'base_url', 'https://api.example.com')
    config.set('api', 'timeout', '30')
    
    config.add_section('output')
    config.set('output', 'format', 'json')
    config.set('output', 'directory', '/tmp/output')
    
    # Python 2 style file writing
    with open('config.ini', 'wb') as configfile:
        config.write(configfile)
    
    print "Config file created: config.ini"


def main():
    """Main function with legacy patterns."""
    # Python 2 style argument parsing (should use argparse)
    if len(sys.argv) < 2:
        print "Usage: %s <config_file>" % sys.argv[0]
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    # Check if config exists
    if not os.path.exists(config_file):
        print "Config file not found: %s" % config_file
        print "Creating sample config..."
        create_config_file()
        return
    
    # Initialize processor
    try:
        processor = LegacyDataProcessor(config_file)
    except Exception, e:  # Python 2 exception syntax
        print "Failed to initialize processor: %s" % e
        sys.exit(1)
    
    # Sample URLs to process
    urls = [
        'https://api.example.com/data/1',
        'https://api.example.com/data/2',
        'https://api.example.com/data/3',
    ]
    
    print "Starting batch processing..."
    results = processor.batch_process(urls)
    
    print "Processing complete. Found %d items." % len(results)
    
    # Export results
    if results:
        output_file = 'results.csv'
        processor.export_to_csv(results, output_file)
        print "Results exported to: %s" % output_file
    
    print "Done!"


if __name__ == '__main__':
    main()

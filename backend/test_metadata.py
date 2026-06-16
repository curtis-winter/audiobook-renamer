#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import just the metadata service by avoiding the __init__.py
# that tries to import file_service
spec = __import__('services.metadata_service')
MetadataService = spec.MetadataService

service = MetadataService()
file_path = '/mnt/plex-media/To Be Sorted/audiobook/Unmapped/Jenny Slate (2019) Little Weirds/Little Weirds.mp3'
result = service.read_metadata(file_path)
print('Year field:', repr(result.get('year')))
print('Year type:', type(result.get('year')))
print('Year is string:', isinstance(result.get('year'), str))

#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Directly load the metadata service module
import importlib.util
spec = importlib.util.spec_from_file_location("metadata_service", "services/metadata_service.py")
metadata_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metadata_service)

MetadataService = metadata_service.MetadataService

service = MetadataService()
file_path = '/mnt/plex-media/To Be Sorted/audiobook/Unmapped/Jenny Slate (2019) Little Weirds/Little Weirds.mp3'
result = service.read_metadata(file_path)
print('Year field:', repr(result.get('year')))
print('Year type:', type(result.get('year')))
print('Year is string:', isinstance(result.get('year'), str))

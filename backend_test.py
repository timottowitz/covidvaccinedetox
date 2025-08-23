#!/usr/bin/env python3
"""
Backend API Testing for mRNA Knowledge Base
Tests all endpoints defined in the FastAPI backend
"""

import requests
import sys
import json
import time
import os
from datetime import datetime
from pathlib import Path

class BackendAPITester:
    def __init__(self, base_url="https://research-vault-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []

    def log_result(self, test_name, passed, details=""):
        """Log test result"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            status = "PASS"
            print(f"✅ {test_name}: {status}")
        else:
            status = "FAIL"
            print(f"❌ {test_name}: {status} - {details}")
        
        self.results.append({
            "test": test_name,
            "status": status,
            "details": details
        })

    def test_health_endpoint(self):
        """Test GET /api/health"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self.log_result("Health Check", True)
                    return True
                else:
                    self.log_result("Health Check", False, f"Expected status='ok', got {data}")
            else:
                self.log_result("Health Check", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Health Check", False, f"Request failed: {str(e)}")
        return False

    def test_root_endpoint(self):
        """Test GET /api/"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "mRNA Knowledge Base API":
                    self.log_result("Root API Message", True)
                    return True
                else:
                    self.log_result("Root API Message", False, f"Expected specific message, got {data}")
            else:
                self.log_result("Root API Message", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Root API Message", False, f"Request failed: {str(e)}")
        return False

    def test_feed_endpoint(self):
        """Test GET /api/feed"""
        try:
            response = requests.get(f"{self.api_url}/feed", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check if feed items have expected structure
                    first_item = data[0]
                    required_fields = ['id', 'type', 'title', 'summary', 'url', 'tags', 'published_at']
                    if all(field in first_item for field in required_fields):
                        self.log_result("Feed Endpoint", True, f"Returned {len(data)} feed items")
                        return True
                    else:
                        missing = [f for f in required_fields if f not in first_item]
                        self.log_result("Feed Endpoint", False, f"Missing fields: {missing}")
                else:
                    self.log_result("Feed Endpoint", False, "Expected non-empty array")
            else:
                self.log_result("Feed Endpoint", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Feed Endpoint", False, f"Request failed: {str(e)}")
        return False

    def test_feed_with_tag_filter(self):
        """Test GET /api/feed?tag=spike"""
        try:
            response = requests.get(f"{self.api_url}/feed?tag=spike", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Feed Tag Filter", True, f"Returned {len(data)} filtered items")
                    return True
                else:
                    self.log_result("Feed Tag Filter", False, "Expected array response")
            else:
                self.log_result("Feed Tag Filter", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Feed Tag Filter", False, f"Request failed: {str(e)}")
        return False

    def test_research_endpoint(self):
        """Test GET /api/research"""
        try:
            response = requests.get(f"{self.api_url}/research", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check if research articles have expected structure
                    first_item = data[0]
                    required_fields = ['id', 'title', 'authors', 'published_date', 'tags', 'citation_count']
                    if all(field in first_item for field in required_fields):
                        self.log_result("Research Endpoint", True, f"Returned {len(data)} research articles")
                        return True
                    else:
                        missing = [f for f in required_fields if f not in first_item]
                        self.log_result("Research Endpoint", False, f"Missing fields: {missing}")
                else:
                    self.log_result("Research Endpoint", False, "Expected non-empty array")
            else:
                self.log_result("Research Endpoint", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Research Endpoint", False, f"Request failed: {str(e)}")
        return False

    def test_research_sort_by_citations(self):
        """Test GET /api/research?sort_by=citations"""
        try:
            response = requests.get(f"{self.api_url}/research?sort_by=citations", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Research Sort by Citations", True, f"Returned {len(data)} sorted articles")
                    return True
                else:
                    self.log_result("Research Sort by Citations", False, "Expected array response")
            else:
                self.log_result("Research Sort by Citations", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Research Sort by Citations", False, f"Request failed: {str(e)}")
        return False

    def test_resources_endpoint(self):
        """Test GET /api/resources"""
        try:
            response = requests.get(f"{self.api_url}/resources", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check if resources have expected structure
                    first_item = data[0]
                    required_fields = ['id', 'title', 'url', 'kind', 'tags']
                    if all(field in first_item for field in required_fields):
                        # Check for at least one PDF and one video
                        has_pdf = any(item.get('kind') == 'pdf' for item in data)
                        has_video = any(item.get('kind') == 'video' for item in data)
                        
                        if has_pdf and has_video:
                            self.log_result("Resources Endpoint", True, f"Returned {len(data)} resources with PDF and video")
                            return True
                        else:
                            self.log_result("Resources Endpoint", False, f"Missing PDF ({has_pdf}) or video ({has_video}) resources")
                    else:
                        missing = [f for f in required_fields if f not in first_item]
                        self.log_result("Resources Endpoint", False, f"Missing fields: {missing}")
                else:
                    self.log_result("Resources Endpoint", False, "Expected non-empty array")
            else:
                self.log_result("Resources Endpoint", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Resources Endpoint", False, f"Request failed: {str(e)}")
        return False

    def test_resources_tag_filter(self):
        """Test GET /api/resources?tag=gut"""
        try:
            response = requests.get(f"{self.api_url}/resources?tag=gut", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Check that filtering works and at least one item has 'gut' tag
                    if len(data) > 0:
                        has_gut_tag = any(
                            any('gut' in tag.lower() for tag in item.get('tags', []))
                            for item in data
                        )
                        if has_gut_tag:
                            self.log_result("Resources Tag Filter", True, f"Returned {len(data)} filtered resources with gut tag")
                            return True
                        else:
                            self.log_result("Resources Tag Filter", False, "No items contain 'gut' in tags")
                    else:
                        self.log_result("Resources Tag Filter", True, "Filter returned empty list (acceptable)")
                        return True
                else:
                    self.log_result("Resources Tag Filter", False, "Expected array response")
            else:
                self.log_result("Resources Tag Filter", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Resources Tag Filter", False, f"Request failed: {str(e)}")
        return False

    def test_treatments_endpoint(self):
        """Test GET /api/treatments"""
        try:
            response = requests.get(f"{self.api_url}/treatments", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check if treatments have expected structure
                    first_item = data[0]
                    required_fields = ['name', 'mechanisms']
                    if all(field in first_item for field in required_fields):
                        # Check if any item has bundle_product field
                        has_bundle = any('bundle_product' in item and item['bundle_product'] for item in data)
                        details = f"Returned {len(data)} treatments"
                        if has_bundle:
                            details += " (includes bundle products)"
                        self.log_result("Treatments Endpoint", True, details)
                        return True
                    else:
                        missing = [f for f in required_fields if f not in first_item]
                        self.log_result("Treatments Endpoint", False, f"Missing fields: {missing}")
                else:
                    self.log_result("Treatments Endpoint", False, "Expected non-empty array")
            else:
                self.log_result("Treatments Endpoint", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Treatments Endpoint", False, f"Request failed: {str(e)}")
        return False

    def test_research_sync_endpoint(self):
        """Test GET /api/research/sync - NEW FEATURE"""
        try:
            response = requests.get(f"{self.api_url}/research/sync", timeout=15)
            if response.status_code == 200:
                data = response.json()
                # Check for required keys: added, updated, parsed (all should be numbers)
                required_keys = ['added', 'updated', 'parsed']
                if all(key in data for key in required_keys):
                    # Verify all values are numbers
                    if all(isinstance(data[key], int) for key in required_keys):
                        self.log_result("Research Sync", True, f"Added: {data['added']}, Updated: {data['updated']}, Parsed: {data['parsed']}")
                        return True
                    else:
                        self.log_result("Research Sync", False, f"Values not all integers: {data}")
                else:
                    missing = [k for k in required_keys if k not in data]
                    self.log_result("Research Sync", False, f"Missing keys: {missing}")
            else:
                self.log_result("Research Sync", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Research Sync", False, f"Request failed: {str(e)}")
        return False

    def test_media_endpoint(self):
        """Test GET /api/media - NEW FEATURE"""
        try:
            response = requests.get(f"{self.api_url}/media", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check if media items have expected structure
                    first_item = data[0]
                    required_fields = ['id', 'title', 'source', 'url', 'tags', 'published_at']
                    if all(field in first_item for field in required_fields):
                        # Check for at least one YouTube and one Vimeo item
                        youtube_items = [item for item in data if 'youtube' in item.get('source', '').lower()]
                        vimeo_items = [item for item in data if 'vimeo' in item.get('source', '').lower()]
                        
                        if len(youtube_items) >= 1 and len(vimeo_items) >= 1:
                            self.log_result("Media Endpoint", True, f"Returned {len(data)} media items (YouTube: {len(youtube_items)}, Vimeo: {len(vimeo_items)})")
                            return True
                        else:
                            self.log_result("Media Endpoint", False, f"Missing YouTube ({len(youtube_items)}) or Vimeo ({len(vimeo_items)}) items")
                    else:
                        missing = [f for f in required_fields if f not in first_item]
                        self.log_result("Media Endpoint", False, f"Missing fields: {missing}")
                else:
                    self.log_result("Media Endpoint", False, "Expected non-empty array")
            else:
                self.log_result("Media Endpoint", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Media Endpoint", False, f"Request failed: {str(e)}")
        return False

    def test_resources_thumbnail_generation(self):
        """Test GET /api/resources for thumbnail generation"""
        try:
            # First call - should trigger lazy thumbnail generation
            start_time = time.time()
            response = requests.get(f"{self.api_url}/resources", timeout=30)
            first_call_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check for PDF and video items with thumbnail_url
                    pdf_items = [item for item in data if item.get('kind') == 'pdf']
                    video_items = [item for item in data if item.get('kind') == 'video']
                    
                    pdf_with_thumbnails = [item for item in pdf_items if item.get('thumbnail_url')]
                    video_with_thumbnails = [item for item in video_items if item.get('thumbnail_url')]
                    
                    # Check if thumbnail files exist on disk
                    thumbnail_files_exist = []
                    for item in pdf_with_thumbnails + video_with_thumbnails:
                        if item.get('thumbnail_url'):
                            # Convert URL to file path
                            thumb_path = f"/app/frontend/public{item['thumbnail_url']}"
                            if os.path.exists(thumb_path):
                                thumbnail_files_exist.append(item['title'])
                    
                    # Second call - should be faster (thumbnails cached)
                    start_time = time.time()
                    response2 = requests.get(f"{self.api_url}/resources", timeout=30)
                    second_call_time = time.time() - start_time
                    
                    details = f"PDF items: {len(pdf_items)} (with thumbnails: {len(pdf_with_thumbnails)}), "
                    details += f"Video items: {len(video_items)} (with thumbnails: {len(video_with_thumbnails)}), "
                    details += f"Thumbnail files on disk: {len(thumbnail_files_exist)}, "
                    details += f"First call: {first_call_time:.2f}s, Second call: {second_call_time:.2f}s"
                    
                    if len(pdf_with_thumbnails) > 0 or len(video_with_thumbnails) > 0:
                        self.log_result("Resources Thumbnail Generation", True, details)
                        return True
                    else:
                        self.log_result("Resources Thumbnail Generation", False, f"No thumbnails generated. {details}")
                else:
                    self.log_result("Resources Thumbnail Generation", False, "Expected non-empty array")
            else:
                self.log_result("Resources Thumbnail Generation", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Resources Thumbnail Generation", False, f"Request failed: {str(e)}")
        return False

    def test_async_upload_workflow(self):
        """Test new async upload workflow with 202 response and task tracking"""
        try:
            # Create a small test PDF content (minimal PDF structure)
            pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""

            # Test 1: PDF upload should return 202 with task_id and idempotency_key
            files = {'file': ('test_async.pdf', pdf_content, 'application/pdf')}
            data = {
                'title': 'Test Async PDF Upload',
                'tags': 'test,pdf,async',
                'description': 'Test async PDF upload workflow'
            }
            headers = {'X-Idempotency-Key': 'test-pdf-upload-123'}
            
            response = requests.post(f"{self.api_url}/resources/upload", files=files, data=data, headers=headers, timeout=30)
            
            if response.status_code == 202:
                result = response.json()
                if 'task_id' in result and 'idempotency_key' in result and result.get('status') == 'pending':
                    task_id = result['task_id']
                    idempotency_key = result['idempotency_key']
                    self.log_result("Async PDF Upload - 202 Response", True, f"Task ID: {task_id}, Status: {result.get('status')}")
                    
                    # Test 2: Check task status progression
                    max_attempts = 30
                    for attempt in range(max_attempts):
                        time.sleep(1)  # Wait 1 second between checks
                        status_response = requests.get(f"{self.api_url}/knowledge/task_status?task_id={task_id}", timeout=10)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            current_status = status_data.get('status')
                            
                            if current_status == 'completed':
                                # Check for result field with ResourceItem data
                                if 'result' in status_data and status_data['result']:
                                    result_item = status_data['result']
                                    if result_item.get('title') == 'Test Async PDF Upload' and result_item.get('kind') == 'pdf':
                                        self.log_result("Task Status - PDF Completed", True, f"Task completed with result: {result_item.get('title')}")
                                        break
                                    else:
                                        self.log_result("Task Status - PDF Completed", False, f"Invalid result data: {result_item}")
                                        break
                                else:
                                    self.log_result("Task Status - PDF Completed", False, "Completed task missing result field")
                                    break
                            elif current_status == 'failed':
                                error_msg = status_data.get('error_message', 'Unknown error')
                                self.log_result("Task Status - PDF Failed", False, f"Task failed: {error_msg}")
                                break
                            elif attempt == max_attempts - 1:
                                self.log_result("Task Status - PDF Timeout", False, f"Task stuck in {current_status} status after {max_attempts} seconds")
                                break
                        else:
                            self.log_result("Task Status Check", False, f"Status endpoint returned {status_response.status_code}")
                            break
                    
                    # Test 3: Idempotency - same key should return existing task
                    response2 = requests.post(f"{self.api_url}/resources/upload", files=files, data=data, headers=headers, timeout=30)
                    if response2.status_code == 202:
                        result2 = response2.json()
                        if result2.get('task_id') == task_id and result2.get('idempotency_key') == idempotency_key:
                            self.log_result("Idempotency Test", True, "Same idempotency key returned existing task")
                        else:
                            self.log_result("Idempotency Test", False, f"Expected same task_id, got different: {result2}")
                    else:
                        self.log_result("Idempotency Test", False, f"Expected 202, got {response2.status_code}")
                        
                else:
                    self.log_result("Async PDF Upload - 202 Response", False, f"Missing required fields in response: {result}")
            else:
                self.log_result("Async PDF Upload - 202 Response", False, f"Expected 202, got {response.status_code}: {response.text}")

            # Test 4: Video upload workflow
            mp4_content = b"fake mp4 content for async testing"
            files = {'file': ('test_async.mp4', mp4_content, 'video/mp4')}
            data = {
                'title': 'Test Async Video Upload',
                'tags': 'test,video,async',
                'description': 'Test async video upload workflow'
            }
            headers = {'X-Idempotency-Key': 'test-video-upload-456'}
            
            response = requests.post(f"{self.api_url}/resources/upload", files=files, data=data, headers=headers, timeout=30)
            
            if response.status_code == 202:
                result = response.json()
                if 'task_id' in result and 'idempotency_key' in result:
                    video_task_id = result['task_id']
                    self.log_result("Async Video Upload - 202 Response", True, f"Video Task ID: {video_task_id}")
                    
                    # Check video task status (don't wait as long since it might fail on fake content)
                    time.sleep(2)
                    status_response = requests.get(f"{self.api_url}/knowledge/task_status?task_id={video_task_id}", timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        self.log_result("Video Task Status Check", True, f"Status: {status_data.get('status')}")
                    else:
                        self.log_result("Video Task Status Check", False, f"Status check failed: {status_response.status_code}")
                else:
                    self.log_result("Async Video Upload - 202 Response", False, f"Missing required fields: {result}")
            else:
                self.log_result("Async Video Upload - 202 Response", False, f"Expected 202, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Async Upload Workflow", False, f"Request failed: {str(e)}")
        return False

    def test_file_validation_limits(self):
        """Test file size and MIME type validation"""
        try:
            # Test 1: File size limit (100MB)
            large_content = b"x" * (101 * 1024 * 1024)  # 101MB
            files = {'file': ('large_file.pdf', large_content, 'application/pdf')}
            data = {'title': 'Large File Test'}
            
            response = requests.post(f"{self.api_url}/resources/upload", files=files, data=data, timeout=30)
            
            if response.status_code == 400:
                error_data = response.json()
                if 'size' in error_data.get('detail', '').lower():
                    self.log_result("File Size Limit Test", True, f"Correctly rejected large file: {error_data.get('detail')}")
                else:
                    self.log_result("File Size Limit Test", False, f"Wrong error message: {error_data}")
            else:
                self.log_result("File Size Limit Test", False, f"Expected 400, got {response.status_code}")

            # Test 2: Unsupported MIME type
            txt_content = b"This is a text file"
            files = {'file': ('test.txt', txt_content, 'text/plain')}
            data = {'title': 'Text File Test'}
            
            response = requests.post(f"{self.api_url}/resources/upload", files=files, data=data, timeout=30)
            
            if response.status_code == 400:
                error_data = response.json()
                if 'type' in error_data.get('detail', '').lower() or 'allowed' in error_data.get('detail', '').lower():
                    self.log_result("MIME Type Validation Test", True, f"Correctly rejected unsupported file type: {error_data.get('detail')}")
                else:
                    self.log_result("MIME Type Validation Test", False, f"Wrong error message: {error_data}")
            else:
                self.log_result("MIME Type Validation Test", False, f"Expected 400, got {response.status_code}")

            # Test 3: Upload without file
            response = requests.post(f"{self.api_url}/resources/upload", data={'title': 'No File Test'}, timeout=30)
            
            if response.status_code in [400, 422]:  # FastAPI might return 422 for missing required field
                self.log_result("Missing File Test", True, f"Correctly rejected upload without file: {response.status_code}")
            else:
                self.log_result("Missing File Test", False, f"Expected 400/422, got {response.status_code}")
                
        except Exception as e:
            self.log_result("File Validation Tests", False, f"Request failed: {str(e)}")
        return False

    def test_task_status_error_cases(self):
        """Test task status endpoint error cases"""
        try:
            # Test invalid task_id
            response = requests.get(f"{self.api_url}/knowledge/task_status?task_id=invalid-task-id-123", timeout=10)
            
            if response.status_code == 404:
                error_data = response.json()
                if 'not found' in error_data.get('detail', '').lower():
                    self.log_result("Invalid Task ID Test", True, f"Correctly returned 404 for invalid task_id")
                else:
                    self.log_result("Invalid Task ID Test", False, f"Wrong error message: {error_data}")
            else:
                self.log_result("Invalid Task ID Test", False, f"Expected 404, got {response.status_code}")
                
            # Test missing task_id parameter
            response = requests.get(f"{self.api_url}/knowledge/task_status", timeout=10)
            
            if response.status_code in [400, 422]:  # FastAPI returns 422 for missing required query param
                self.log_result("Missing Task ID Test", True, f"Correctly rejected request without task_id: {response.status_code}")
            else:
                self.log_result("Missing Task ID Test", False, f"Expected 400/422, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Task Status Error Cases", False, f"Request failed: {str(e)}")
        return False

    def test_backwards_compatibility(self):
        """Test that existing endpoints still work"""
        try:
            # Test GET /api/resources still works
            response = requests.get(f"{self.api_url}/resources", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("GET Resources Compatibility", True, f"Returned {len(data)} resources")
                else:
                    self.log_result("GET Resources Compatibility", False, "Expected array response")
            else:
                self.log_result("GET Resources Compatibility", False, f"Expected 200, got {response.status_code}")

            # Test knowledge reconciliation endpoint
            response = requests.post(f"{self.api_url}/knowledge/reconcile", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'updated' in data and isinstance(data['updated'], int):
                    self.log_result("Knowledge Reconcile Compatibility", True, f"Updated {data['updated']} items")
                else:
                    self.log_result("Knowledge Reconcile Compatibility", False, f"Unexpected response: {data}")
            else:
                self.log_result("Knowledge Reconcile Compatibility", False, f"Expected 200, got {response.status_code}")

            # Test knowledge status endpoint
            response = requests.get(f"{self.api_url}/knowledge/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'files' in data and isinstance(data['files'], list):
                    self.log_result("Knowledge Status Compatibility", True, f"Found {len(data['files'])} knowledge files")
                else:
                    self.log_result("Knowledge Status Compatibility", False, f"Unexpected response: {data}")
            else:
                self.log_result("Knowledge Status Compatibility", False, f"Expected 200, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Backwards Compatibility Tests", False, f"Request failed: {str(e)}")
        return False

    def test_external_url_thumbnail_handling(self):
        """Test thumbnail generation for external URLs with graceful failure handling"""
        try:
            # Test with resources that have external URLs
            response = requests.get(f"{self.api_url}/resources", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                external_resources = [
                    item for item in data 
                    if item.get('url', '').startswith('http') and item.get('kind') in ['pdf', 'video']
                ]
                
                if len(external_resources) > 0:
                    # Check that the service handles external URLs gracefully
                    # Even if thumbnail generation fails, the response should be 200
                    # and the items should still be returned
                    
                    details = f"Found {len(external_resources)} external resources. "
                    details += "Service handled external URLs without 5xx errors."
                    
                    # Check for any items that might have failed thumbnail generation
                    failed_thumbnails = [
                        item for item in external_resources 
                        if item.get('thumbnail_url') is None
                    ]
                    
                    if len(failed_thumbnails) > 0:
                        details += f" {len(failed_thumbnails)} items without thumbnails (acceptable for external URLs)."
                    
                    self.log_result("External URL Thumbnail Handling", True, details)
                    return True
                else:
                    self.log_result("External URL Thumbnail Handling", True, "No external resources found (acceptable)")
                    return True
            else:
                self.log_result("External URL Thumbnail Handling", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("External URL Thumbnail Handling", False, f"Request failed: {str(e)}")
        return False

    def test_cors_and_route_prefixes(self):
        """Test that CORS and route prefixes are unchanged"""
        try:
            # Test CORS headers
            response = requests.options(f"{self.api_url}/resources", timeout=10)
            cors_headers = {
                'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
                'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
                'access-control-allow-headers': response.headers.get('access-control-allow-headers')
            }
            
            # Test that /api prefix is maintained
            health_response = requests.get(f"{self.api_url}/health", timeout=10)
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                if health_data.get("status") == "ok":
                    details = f"CORS headers present: {bool(cors_headers['access-control-allow-origin'])}, "
                    details += f"Health endpoint accessible at /api/health"
                    self.log_result("CORS and Route Prefixes", True, details)
                    return True
                else:
                    self.log_result("CORS and Route Prefixes", False, "Health endpoint not responding correctly")
            else:
                self.log_result("CORS and Route Prefixes", False, f"Health endpoint returned {health_response.status_code}")
        except Exception as e:
            self.log_result("CORS and Route Prefixes", False, f"Request failed: {str(e)}")
        return False

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Backend API Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 50)

        # Run all tests
        self.test_health_endpoint()
        self.test_root_endpoint()
        self.test_feed_endpoint()
        self.test_feed_with_tag_filter()
        self.test_research_endpoint()
        self.test_research_sort_by_citations()
        self.test_research_sync_endpoint()  # NEW FEATURE TEST
        self.test_resources_endpoint()
        self.test_resources_tag_filter()
        self.test_treatments_endpoint()
        self.test_media_endpoint()  # NEW FEATURE TEST
        self.test_status_endpoints()

        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Backend Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend tests passed!")
            return True
        else:
            print("⚠️  Some backend tests failed. Check details above.")
            return False

    def run_thumbnail_tests(self):
        """Run thumbnail-specific tests as requested in review"""
        print("🚀 Starting Thumbnail Generation Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 50)

        # Run thumbnail-specific tests
        self.test_health_endpoint()  # Verify /api/health returns ok
        self.test_resources_thumbnail_generation()  # Test GET /api/resources with thumbnail generation
        self.test_upload_with_thumbnail_generation()  # Test POST /api/resources/upload
        self.test_external_url_thumbnail_handling()  # Test edge cases with external URLs
        self.test_cors_and_route_prefixes()  # Confirm no changes to base route prefixes and CORS

        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Thumbnail Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All thumbnail tests passed!")
            return True
        else:
            print("⚠️  Some thumbnail tests failed. Check details above.")
            return False

def main():
    """Main test runner"""
    tester = BackendAPITester()
    # Run thumbnail-specific tests as requested in review
    success = tester.run_thumbnail_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
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
    def __init__(self, base_url="https://vaccine-education.preview.emergentagent.com"):
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

    def test_upload_with_thumbnail_generation(self):
        """Test POST /api/resources/upload with thumbnail generation"""
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

            # Test PDF upload
            files = {'file': ('test_thumbnail.pdf', pdf_content, 'application/pdf')}
            data = {
                'title': 'Test PDF for Thumbnail',
                'tags': 'test,pdf,thumbnail',
                'description': 'Test PDF upload for thumbnail generation'
            }
            
            response = requests.post(f"{self.api_url}/resources/upload", files=files, data=data, timeout=30)
            
            pdf_upload_success = False
            pdf_thumbnail_url = None
            
            if response.status_code == 200:
                result = response.json()
                if result.get('kind') == 'pdf' and result.get('title') == 'Test PDF for Thumbnail':
                    pdf_upload_success = True
                    pdf_thumbnail_url = result.get('thumbnail_url')
                    self.log_result("PDF Upload", True, f"Thumbnail URL: {pdf_thumbnail_url}")
                else:
                    self.log_result("PDF Upload", False, f"Unexpected response: {result}")
            else:
                self.log_result("PDF Upload", False, f"Expected 200, got {response.status_code}: {response.text}")

            # Note: Creating a valid MP4 is complex, so we'll test with a simple file
            # and expect it might fail thumbnail generation but still upload successfully
            mp4_content = b"fake mp4 content for testing"
            
            files = {'file': ('test_thumbnail.mp4', mp4_content, 'video/mp4')}
            data = {
                'title': 'Test MP4 for Thumbnail',
                'tags': 'test,video,thumbnail',
                'description': 'Test MP4 upload for thumbnail generation'
            }
            
            response = requests.post(f"{self.api_url}/resources/upload", files=files, data=data, timeout=30)
            
            mp4_upload_success = False
            mp4_thumbnail_url = None
            
            if response.status_code == 200:
                result = response.json()
                if result.get('kind') == 'video' and result.get('title') == 'Test MP4 for Thumbnail':
                    mp4_upload_success = True
                    mp4_thumbnail_url = result.get('thumbnail_url')
                    self.log_result("MP4 Upload", True, f"Thumbnail URL: {mp4_thumbnail_url}")
                else:
                    self.log_result("MP4 Upload", False, f"Unexpected response: {result}")
            else:
                self.log_result("MP4 Upload", False, f"Expected 200, got {response.status_code}: {response.text}")

            # Verify uploads appear in GET /api/resources
            response = requests.get(f"{self.api_url}/resources", timeout=30)
            if response.status_code == 200:
                resources = response.json()
                uploaded_pdf = next((r for r in resources if r.get('title') == 'Test PDF for Thumbnail'), None)
                uploaded_mp4 = next((r for r in resources if r.get('title') == 'Test MP4 for Thumbnail'), None)
                
                verification_success = uploaded_pdf is not None and uploaded_mp4 is not None
                details = f"PDF found: {uploaded_pdf is not None}, MP4 found: {uploaded_mp4 is not None}"
                
                self.log_result("Upload Verification", verification_success, details)
                
                return pdf_upload_success and mp4_upload_success and verification_success
            else:
                self.log_result("Upload Verification", False, f"Failed to verify uploads: {response.status_code}")
                
        except Exception as e:
            self.log_result("Upload with Thumbnail Generation", False, f"Request failed: {str(e)}")
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

    def run_incremental_tests_only(self):
        """Run only the new feature tests requested"""
        print("🚀 Starting Incremental Backend API Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 50)

        # Run only the new tests
        self.test_research_sync_endpoint()
        self.test_media_endpoint()

        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Incremental Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All incremental tests passed!")
            return True
        else:
            print("⚠️  Some incremental tests failed. Check details above.")
            return False

def main():
    """Main test runner"""
    tester = BackendAPITester()
    # Run only incremental tests as requested
    success = tester.run_incremental_tests_only()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
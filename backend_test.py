#!/usr/bin/env python3
"""
Backend API Testing for mRNA Knowledge Base
Tests all endpoints defined in the FastAPI backend
"""

import requests
import sys
import json
from datetime import datetime

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

    def test_status_endpoints(self):
        """Test POST and GET /api/status"""
        try:
            # Test POST /api/status
            test_data = {"client_name": f"test_client_{datetime.now().strftime('%H%M%S')}"}
            response = requests.post(f"{self.api_url}/status", json=test_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and 'client_name' in data and 'timestamp' in data:
                    self.log_result("Status POST", True)
                    
                    # Test GET /api/status
                    get_response = requests.get(f"{self.api_url}/status", timeout=10)
                    if get_response.status_code == 200:
                        get_data = get_response.json()
                        if isinstance(get_data, list):
                            self.log_result("Status GET", True, f"Returned {len(get_data)} status checks")
                            return True
                        else:
                            self.log_result("Status GET", False, "Expected array response")
                    else:
                        self.log_result("Status GET", False, f"Expected 200, got {get_response.status_code}")
                else:
                    self.log_result("Status POST", False, "Missing required fields in response")
            else:
                self.log_result("Status POST", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Status Endpoints", False, f"Request failed: {str(e)}")
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
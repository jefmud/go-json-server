package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

const testToken = "secret-token"

// newTestServer sets up a server pointing at a temp JSON dir seeded with db.json.
func newTestServer(t *testing.T) *server {
	t.Helper()

	dir := t.TempDir()
	seed := map[string]interface{}{
		"posts": []interface{}{
			map[string]interface{}{"id": 1, "title": "one"},
			map[string]interface{}{"id": 2, "title": "two"},
		},
		"meta": map[string]interface{}{"version": "v1"},
		"profile": []interface{}{
			map[string]interface{}{"id": 1, "name": "json-server"},
		},
	}
	buf, err := json.Marshal(seed)
	if err != nil {
		t.Fatalf("marshal seed: %v", err)
	}
	if err := os.WriteFile(filepath.Join(dir, "db.json"), buf, 0644); err != nil {
		t.Fatalf("write seed: %v", err)
	}

	return &server{
		jsonDir: dir,
		token:   testToken,
	}
}

func authedRequest(method, target string, body []byte) *http.Request {
	var reader *bytes.Reader
	if body != nil {
		reader = bytes.NewReader(body)
	} else {
		reader = bytes.NewReader(nil)
	}
	req := httptest.NewRequest(method, target, reader)
	req.Header.Set("Authorization", "Bearer "+testToken)
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	return req
}

func decodeJSON(t *testing.T, body *bytes.Buffer, dest interface{}) {
	t.Helper()
	if err := json.Unmarshal(body.Bytes(), dest); err != nil {
		t.Fatalf("decode response: %v", err)
	}
}

func TestUnauthorized(t *testing.T) {
	s := newTestServer(t)
	rr := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/api/db", nil)

	s.ServeHTTP(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", rr.Code)
	}
}

func TestGetDatabaseRoot(t *testing.T) {
	s := newTestServer(t)
	rr := httptest.NewRecorder()
	req := authedRequest(http.MethodGet, "/api/db", nil)

	s.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}
	var payload map[string]interface{}
	decodeJSON(t, rr.Body, &payload)
	posts, ok := payload["posts"].([]interface{})
	if !ok {
		t.Fatalf("posts should be array, got %T", payload["posts"])
	}
	if len(posts) != 2 {
		t.Fatalf("expected 2 posts, got %d", len(posts))
	}
}

func TestCreateAutoIncrementID(t *testing.T) {
	s := newTestServer(t)
	rr := httptest.NewRecorder()
	req := authedRequest(http.MethodPost, "/api/db/posts", []byte(`{"title":"third"}`))

	s.ServeHTTP(rr, req)

	if rr.Code != http.StatusCreated {
		t.Fatalf("expected 201, got %d", rr.Code)
	}
	var created map[string]interface{}
	decodeJSON(t, rr.Body, &created)
	if created["id"] != float64(3) { // json.Unmarshal converts numbers to float64
		t.Fatalf("expected id 3, got %#v", created["id"])
	}
}

func TestPatchDoesNotChangeID(t *testing.T) {
	s := newTestServer(t)
	rr := httptest.NewRecorder()
	req := authedRequest(http.MethodPatch, "/api/db/posts/1", []byte(`{"id":999,"title":"updated"}`))

	s.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}
	var patched map[string]interface{}
	decodeJSON(t, rr.Body, &patched)
	if patched["id"] != float64(1) {
		t.Fatalf("expected id to remain 1, got %#v", patched["id"])
	}
	if patched["title"] != "updated" {
		t.Fatalf("expected title updated, got %#v", patched["title"])
	}
}

func TestSortingAndPagination(t *testing.T) {
	s := newTestServer(t)
	rr := httptest.NewRecorder()
	req := authedRequest(http.MethodGet, "/api/db/posts?_sort=id&_order=desc&_limit=1", nil)

	s.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}
	var items []map[string]interface{}
	decodeJSON(t, rr.Body, &items)
	if len(items) != 1 {
		t.Fatalf("expected 1 item, got %d", len(items))
	}
	if items[0]["id"] != float64(2) {
		t.Fatalf("expected id 2, got %#v", items[0]["id"])
	}
}

func TestCreatesNewDatabaseOnWrite(t *testing.T) {
	s := newTestServer(t)
	rr := httptest.NewRecorder()
	req := authedRequest(http.MethodPost, "/api/newdb/widgets", []byte(`{"name":"first"}`))

	s.ServeHTTP(rr, req)

	if rr.Code != http.StatusCreated {
		t.Fatalf("expected 201, got %d", rr.Code)
	}
	path := filepath.Join(s.jsonDir, "newdb.json")
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("expected newdb.json to be created, got error %v", err)
	}
}

func TestDeleteRemovesItem(t *testing.T) {
	s := newTestServer(t)

	// Delete existing post
	rr := httptest.NewRecorder()
	req := authedRequest(http.MethodDelete, "/api/db/posts/1", nil)
	s.ServeHTTP(rr, req)
	if rr.Code != http.StatusNoContent {
		t.Fatalf("expected 204, got %d", rr.Code)
	}

	// Confirm it is gone
	rr = httptest.NewRecorder()
	req = authedRequest(http.MethodGet, "/api/db/posts/1", nil)
	s.ServeHTTP(rr, req)
	if rr.Code != http.StatusNotFound {
		t.Fatalf("expected 404 after delete, got %d", rr.Code)
	}
}

func TestBadRequestInvalidJSON(t *testing.T) {
	s := newTestServer(t)
	rr := httptest.NewRecorder()
	req := authedRequest(http.MethodPost, "/api/db/posts", []byte(`{"title":`)) // malformed

	s.ServeHTTP(rr, req)

	if rr.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", rr.Code)
	}
}

func TestBadRequestNonArrayCollection(t *testing.T) {
	s := newTestServer(t)
	rr := httptest.NewRecorder()
	req := authedRequest(http.MethodGet, "/api/db/meta", nil)

	s.ServeHTTP(rr, req)

	if rr.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", rr.Code)
	}
}

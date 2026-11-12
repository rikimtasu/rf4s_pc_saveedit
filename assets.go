package main

import (
	"archive/zip"
	"bytes"
	_ "embed"
	"io"
)

// The build uses the same algorithms and curated assets as the Qt editor.
//
//go:embed web/mygo-bundle.js
var coreScript string

//go:embed build/mygo-assets.zip
var assetBytes []byte

func asset(name string) ([]byte, error) {
	r, err := zip.NewReader(bytes.NewReader(assetBytes), int64(len(assetBytes)))
	if err != nil {
		return nil, err
	}
	f, err := r.Open(name)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return io.ReadAll(f)
}

package main

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"io"
	"strings"
	"unicode/utf8"

	"github.com/dop251/goja"
)

// Core is confined to the UI thread. File dialogs return through Window.Update;
// neither the JS runtime nor its document is shared with background goroutines.
type Core struct {
	vm     *goja.Runtime
	invoke goja.Callable
}

func newCore() (*Core, error) {
	vm := goja.New()
	vm.Set("encodeUTF8", func(s string) []int {
		b := []byte(s)
		a := make([]int, len(b))
		for i := range b {
			a[i] = int(b[i])
		}
		return a
	})
	vm.Set("decodeUTF8", func(s string, fatal bool) string {
		var a []int
		_ = json.Unmarshal([]byte(s), &a)
		b := make([]byte, len(a))
		for i := range a {
			b[i] = byte(a[i])
		}
		if fatal && !utf8.Valid(b) {
			panic(vm.NewTypeError("Invalid UTF-8 text"))
		}
		return strings.TrimPrefix(strings.ToValidUTF8(string(b), string(utf8.RuneError)), "\ufeff")
	})
	_, err := vm.RunString(`var TextEncoder = class { encode(s) { return Uint8Array.from(encodeUTF8(s)); } }; var TextDecoder = class { constructor(encoding, options) { this.fatal = !!(options && options.fatal); } decode(b) { return decodeUTF8(JSON.stringify(Array.from(b)), this.fatal); } };` + coreScript)
	if err != nil {
		return nil, fmt.Errorf("load save algorithms: %w", err)
	}
	fn, ok := goja.AssertFunction(vm.Get("RF4SMygo").ToObject(vm).Get("invokeJSON"))
	if !ok {
		return nil, fmt.Errorf("missing MyGO core entry point")
	}
	c := &Core{vm: vm, invoke: fn}
	if data, err := asset("references.json.gz"); err == nil {
		r, err := gzip.NewReader(bytes.NewReader(data))
		if err != nil {
			return nil, err
		}
		defer r.Close()
		data, err = io.ReadAll(r)
		if err != nil {
			return nil, err
		}
		if _, err = c.JSON("initialize", json.RawMessage(data)); err != nil {
			return nil, err
		}
	}
	return c, nil
}

func (c *Core) JSON(op string, args any) (json.RawMessage, error) {
	if args == nil {
		args = map[string]any{}
	}
	b, err := json.Marshal(args)
	if err != nil {
		return nil, err
	}
	v, err := c.invoke(goja.Undefined(), c.vm.ToValue(op), c.vm.ToValue(string(b)))
	if err != nil {
		return nil, fmt.Errorf("%s", err)
	}
	return json.RawMessage(v.String()), nil
}

func (c *Core) Call(op string, args, out any) error {
	b, err := c.JSON(op, args)
	if err != nil {
		return err
	}
	if out == nil {
		return nil
	}
	return json.Unmarshal(b, out)
}

func (c *Core) Bytes(op string, args any) ([]byte, error) {
	var a []int
	if err := c.Call(op, args, &a); err != nil {
		return nil, err
	}
	b := make([]byte, len(a))
	for i, n := range a {
		b[i] = byte(n)
	}
	return b, nil
}

func integers(b []byte) []int {
	a := make([]int, len(b))
	for i := range b {
		a[i] = int(b[i])
	}
	return a
}

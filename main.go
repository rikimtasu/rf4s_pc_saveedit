package main

import (
	"flag"
	"image/png"
	"log"
	"os"
	"path/filepath"

	"github.com/egoist/mygo"
	"github.com/egoist/mygo/ui"
)

const appVersion = "0.5.0"

func main() {
	screenshot := flag.String("screenshot", "", "Render a synthetic demo to a PNG without opening a window or writing saves")
	flag.Parse()
	for _, f := range []struct{ file, family string }{{"NotoSans.ttf", "Noto Sans"}, {"NotoSansCJKsc-Medium.otf", "Noto Sans CJK SC"}} {
		b, err := asset("fonts/" + f.file)
		if err != nil {
			log.Fatal(err)
		}
		if err = ui.RegisterFont(b, f.family); err != nil {
			log.Fatal(err)
		}
	}
	core, err := newCore()
	if err != nil {
		log.Fatal(err)
	}
	editor, err := newEditor(core)
	if err != nil {
		log.Fatal(err)
	}
	if *screenshot != "" {
		b, err := core.Bytes("demoBytes", nil)
		if err != nil {
			log.Fatal(err)
		}
		if err = editor.openBytes(b, "Synthetic demo.sav", true); err != nil {
			log.Fatal(err)
		}
		editor.navigate("inventory")
		tt := ui.NewTester(editor.view, 1180, 820)
		if err := os.MkdirAll(filepath.Dir(*screenshot), 0700); err != nil {
			log.Fatal(err)
		}
		f, err := os.Create(*screenshot)
		if err != nil {
			log.Fatal(err)
		}
		defer f.Close()
		if err := png.Encode(f, tt.Image()); err != nil {
			log.Fatal(err)
		}
		return
	}
	mygo.App.WhenReady(func() {
		editor.win = mygo.NewWindow(mygo.WindowOptions{Title: "Rune Factory 4 Special · MyGO · v" + appVersion, Width: 1180, Height: 850, MinWidth: 640, MinHeight: 480, BackgroundColor: "#2e3440", Content: ui.View(editor.view)})
		editor.win.OnClose(func(e *mygo.CloseEvent) {
			if editor.busy {
				e.PreventDefault()
				return
			}
			if editor.unexported() {
				e.PreventDefault()
				editor.confirm("Discard unexported edits and drafts?", func() { editor.win.Destroy() })
			}
		})
	})
	if err := mygo.App.Run(); err != nil {
		log.Fatal(err)
	}
}

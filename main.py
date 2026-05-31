#!/usr/bin/env python3
"""PDF Toolkit — CLI entry point."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _default_output(input_path: str, operation: str, ext: str = ".pdf") -> str:
    p = Path(input_path)
    return str(p.parent / f"{p.stem}_{operation}{ext}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pdf-toolkit",
        description="Python PDF editing toolkit",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # compress
    p = sub.add_parser("compress", help="Compress a PDF")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument(
        "--quality",
        choices=["screen", "ebook", "printer", "prepress"],
        default="printer",
    )
    p.add_argument("--dry-run", action="store_true")

    # crop
    p = sub.add_parser("crop", help="Crop pages")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--box", help="x1,y1,x2,y2 in PDF points")
    p.add_argument("--pages", default="all")
    p.add_argument("--gui", action="store_true")
    p.add_argument("--dry-run", action="store_true")

    # rotate
    p = sub.add_parser("rotate", help="Rotate pages")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--angle", type=int, required=True, choices=[90, 180, 270, -90])
    p.add_argument("--pages", default="all")
    p.add_argument("--dry-run", action="store_true")

    # unlock
    p = sub.add_parser("unlock", help="Remove password protection")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--password", default="")
    p.add_argument("--dry-run", action="store_true")

    # split
    p = sub.add_parser("split", help="Split PDF into parts")
    p.add_argument("input")
    p.add_argument("--output-dir")
    p.add_argument(
        "--mode", choices=["pages", "range", "size"], default="pages"
    )
    p.add_argument("--ranges")
    p.add_argument("--chunk-size", type=int)
    p.add_argument("--dry-run", action="store_true")

    # merge
    p = sub.add_parser("merge", help="Merge PDFs")
    p.add_argument("inputs", nargs="+")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--interleave", action="store_true")
    p.add_argument("--dry-run", action="store_true")

    # watermark
    p = sub.add_parser("watermark", help="Add watermark")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--text")
    p.add_argument("--image")
    p.add_argument("--font-size", type=int, default=48)
    p.add_argument("--opacity", type=float, default=0.3)
    p.add_argument("--color", default="#FF0000")
    p.add_argument(
        "--position",
        choices=["center", "top-right", "bottom-left"],
        default="center",
    )
    p.add_argument("--scale", type=float, default=0.2)
    p.add_argument("--pages", default="all")
    p.add_argument("--dry-run", action="store_true")

    # extract
    p = sub.add_parser("extract", help="Extract content")
    p.add_argument("input")
    p.add_argument(
        "--type",
        dest="type_",
        choices=["text", "images", "tables", "pages"],
        default="text",
    )
    p.add_argument("--output")
    p.add_argument("--pages", default="all")
    p.add_argument("--dry-run", action="store_true")

    # metadata
    p = sub.add_parser("metadata", help="Read or edit PDF metadata")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--read", action="store_true")
    p.add_argument("--set", nargs="+", metavar="key=value", dest="fields")
    p.add_argument("--dry-run", action="store_true")

    # img2pdf
    p = sub.add_parser("img2pdf", help="Convert image(s) or a folder of images to a PDF")
    p.add_argument("inputs", nargs="+", metavar="image_or_folder")
    p.add_argument("-o", "--output", required=True)
    p.add_argument(
        "--size",
        default="fit",
        help="Page size: fit (use image dimensions), a4, a4-landscape, letter, or WxH in points (default: fit)",
    )
    p.add_argument("--dry-run", action="store_true")

    # repair
    p = sub.add_parser("repair", help="Attempt to repair a corrupted PDF")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--dry-run", action="store_true")

    # pdf2img
    p = sub.add_parser("pdf2img", help="Convert PDF pages to images")
    p.add_argument("input")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--format", dest="fmt", choices=["png", "jpg", "webp", "tiff"], default="png")
    p.add_argument("--dpi", type=int, default=150)
    p.add_argument("--pages", default="all")
    p.add_argument("--dry-run", action="store_true")

    # normalize
    p = sub.add_parser("normalize", help="Resize all pages to the same size")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument(
        "--size",
        default="a4",
        help="Target page size: a4, a4-landscape, a3, a3-landscape, letter, legal, or WxH in PDF points (default: a4)",
    )
    p.add_argument("--dry-run", action="store_true")

    # info
    p = sub.add_parser("info", help="Detect PDF type and show info")
    p.add_argument("input")

    args = parser.parse_args()
    try:
        _dispatch(args)
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _dispatch(args: argparse.Namespace) -> None:
    cmd = args.command

    if cmd == "compress":
        from utils.compress import compress
        out = args.output or _default_output(args.input, "compressed")
        compress(args.input, out, quality=args.quality, dry_run=args.dry_run)

    elif cmd == "crop":
        from utils.crop import crop
        out = args.output or _default_output(args.input, "cropped")
        crop(
            args.input, out,
            box=args.box, pages=args.pages,
            gui=args.gui, dry_run=args.dry_run,
        )

    elif cmd == "rotate":
        from utils.rotate import rotate
        out = args.output or _default_output(args.input, "rotated")
        rotate(
            args.input, out,
            angle=args.angle, pages=args.pages, dry_run=args.dry_run,
        )

    elif cmd == "unlock":
        from utils.unlock import unlock
        out = args.output or _default_output(args.input, "unlocked")
        unlock(args.input, out, password=args.password, dry_run=args.dry_run)

    elif cmd == "split":
        from utils.split import split
        out_dir = args.output_dir or str(Path(args.input).parent)
        split(
            args.input, out_dir,
            mode=args.mode, ranges=args.ranges,
            chunk_size=args.chunk_size, dry_run=args.dry_run,
        )

    elif cmd == "merge":
        from utils.merge import merge
        merge(
            args.inputs, args.output,
            interleave=args.interleave, dry_run=args.dry_run,
        )

    elif cmd == "watermark":
        from utils.watermark import watermark
        out = args.output or _default_output(args.input, "watermarked")
        watermark(
            args.input, out,
            text=args.text, image=args.image,
            font_size=args.font_size, opacity=args.opacity,
            color=args.color, position=args.position,
            scale=args.scale, pages=args.pages,
            dry_run=args.dry_run,
        )

    elif cmd == "extract":
        from utils.extract import extract
        ext = ".txt" if args.type_ == "text" else ""
        out = args.output or _default_output(
            args.input, f"extracted_{args.type_}", ext
        )
        extract(
            args.input, out,
            type_=args.type_, pages=args.pages, dry_run=args.dry_run,
        )

    elif cmd == "metadata":
        from utils.metadata import read_metadata, write_metadata
        if args.read or not args.fields:
            for k, v in read_metadata(args.input).items():
                print(f"  {k}: {v}")
        if args.fields:
            out = args.output or _default_output(args.input, "meta")
            parsed: dict[str, str] = {}
            for item in args.fields:
                if "=" not in item:
                    raise ValueError(
                        f"Invalid --set format '{item}'. Use key=value."
                    )
                k, v = item.split("=", 1)
                parsed[k] = v
            write_metadata(
                args.input, out, dry_run=args.dry_run, **parsed
            )

    elif cmd == "img2pdf":
        from utils.convert import img_to_pdf
        img_to_pdf(args.inputs, args.output, size=args.size, dry_run=args.dry_run)

    elif cmd == "repair":
        from utils.repair import repair
        out = args.output or _default_output(args.input, "repaired")
        repair(args.input, out, dry_run=args.dry_run)

    elif cmd == "pdf2img":
        from utils.convert import pdf_to_img
        pdf_to_img(
            args.input, args.output_dir,
            fmt=args.fmt, dpi=args.dpi,
            pages=args.pages, dry_run=args.dry_run,
        )

    elif cmd == "normalize":
        from utils.normalize import normalize
        out = args.output or _default_output(args.input, "normalized")
        normalize(args.input, out, size=args.size, dry_run=args.dry_run)

    elif cmd == "info":
        from utils.pdf_info import detect_pdf_type
        info = detect_pdf_type(args.input)
        print(f"File:         {args.input}")
        print(f"Type:         {info.type}")
        print(f"Pages:        {info.page_count}")
        print(f"Encrypted:    {info.encryption_type or 'No'}")
        print(f"Has forms:    {info.has_forms}")
        print(f"Text pages:   {info.text_page_count}")
        print(f"Image pages:  {info.image_only_page_count}")


if __name__ == "__main__":
    main()

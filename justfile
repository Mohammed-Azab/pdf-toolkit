python := ".venv/bin/python3"

default:
    @just --list

compress file quality="printer":
    {{python}} main.py compress "{{file}}" --quality {{quality}}

crop file box pages="all":
    {{python}} main.py crop "{{file}}" --box {{box}} --pages {{pages}}

rotate file angle pages="all":
    {{python}} main.py rotate "{{file}}" --angle {{angle}} --pages {{pages}}

unlock file password="":
    {{python}} main.py unlock "{{file}}" {{ if password != "" { "--password " + password } else { "" } }}

split file mode="pages" ranges="" output_dir="":
    {{python}} main.py split "{{file}}" --mode {{mode}} {{ if ranges != "" { "--ranges " + ranges } else { "" } }} {{ if output_dir != "" { "--output-dir " + output_dir } else { "" } }}

merge output +files:
    {{python}} main.py merge {{files}} -o "{{output}}"

watermark file text:
    {{python}} main.py watermark "{{file}}" --text "{{text}}"

watermark-img file image:
    {{python}} main.py watermark "{{file}}" --image "{{image}}"

extract file type="text" pages="all":
    {{python}} main.py extract "{{file}}" --type {{type}} --pages {{pages}}

meta-read file:
    {{python}} main.py metadata "{{file}}" --read

meta-set file +fields:
    {{python}} main.py metadata "{{file}}" --set {{fields}}

img2pdf output +images:
    {{python}} main.py img2pdf {{images}} -o "{{output}}"

pdf2img file output_dir fmt="png" dpi="150":
    {{python}} main.py pdf2img "{{file}}" --output-dir "{{output_dir}}" --format {{fmt}} --dpi {{dpi}}

repair file:
    {{python}} main.py repair "{{file}}"

normalize file size="a4":
    {{python}} main.py normalize "{{file}}" --size {{size}}

info file:
    {{python}} main.py info "{{file}}"

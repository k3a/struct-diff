# struct_diff

Copares two objects and produces a dictionary describing changes.
Ideal for comparing two JSON or YAML objects and generating a structural human-readable diff.

This is a Python port of [json-diff](https://github.com/andreyvit/json-diff) JavaScript library.

## Purpose

It produces diff like this:

```json
{
  "type__deleted": "donut",
  "name": {
    "__old": "Cake",
    "__new": "Donut"
  },
  "arr": [
    [
      " "
    ],
    [
      "-",
      2
    ],
    [
      "+",
      {
        "obj": "ok",
        "secondkey": 123
      }
    ],
    [
      " "
    ],
    [
      "+",
      4
    ]
  ],
  "image": {
    "caption": {
      "width": {
        "__old": 123,
        "__new": 321
      },
      "height": {
        "__old": 321,
        "__new": {
          "value": 642,
          "units": "mm"
        }
      }
    }
  },
  "thumbnail": {
    "extra__added": {
      "price": 111,
      "sizes": [
        "L",
        "XL"
      ]
    },
    "width": {
      "__old": 32,
      "__new": 64
    }
  }
}
```

and from that it can generate a human-readable structural JSON diff:

```diff
 {
-  type: "donut"
-  name: "Cake"
+  name: "Donut"
   arr: [
     ...
-    2
+    {
+      obj: "ok"
+      secondkey: 123
+    }
     ...
+    4
   ]
   image: {
     caption: {
-      width: 123
+      width: 321
-      height: 321
+      height: {
+        value: 642
+        units: "mm"
+      }
     }
   }
   thumbnail: {
+    extra: {
+      price: 111
+      sizes: [
+        "L"
+        "XL"
+      ]
+    }
-    width: 32
+    width: 64
   }
 }
```

or structural YAML diff:

```diff
-  type: "donut"
-  name: "Cake"
+  name: "Donut"
   arr: 
     ...
-    - 2
+    - obj: "ok"
+      secondkey: 123
     ...
+    - 4
   image: 
     caption: 
-      width: 123
+      width: 321
-      height: 321
+      height: 
+        value: 642
+        units: "mm"
   thumbnail: 
+    extra: 
+      price: 111
+      sizes: 
+        - "L"
+        - "XL"
-    width: 32
+    width: 64
```

## Usage

Simple:

```python3 -m struct_diff a.json b.json```

Detailed:

```txt
% python3 -m struct_diff -h

usage: struct_diff [-h] [-C] [--no-color] [-j] [-Y] [-f] [--max-elisions MAX_ELISIONS] [-o KEY [KEY ...]] [-n] [-s] [-k] [-K] [-p DECIMALS] old new

positional arguments:
  old                   original file
  new                   new file

optional arguments:
  -h, --help            show this help message and exit
  -C                    force colorize the output
  --no-color            do not colorize the output
  -j, --raw-json        display raw JSON encoding of the diff
  -Y, --yaml            output diff as YAML
  -f, --full            include the equal sections of the document, not just the deltas
  --max-elisions MAX_ELISIONS
                        max number of ...'s to show in a row in "deltas" mode (before collapsing them) #var(maxElisions)
  -o KEY [KEY ...], --output-keys KEY [KEY ...]
                        always print this comma separated keys, with their value, if they are part of an object with any diff
  -n, --output-new-only
                        output only the updated and new key/value pairs (without marking them as such). If you need only the diffs from the old file, just exchange the first and second json
  -s, --sort            sort primitive values in arrays before comparing
  -k, --keys-only       compare only the keys, ignore the differences in values
  -K, --keep-unchanged-values
                        instead of omitting values that are equal, output them as they are
  -p DECIMALS, --precision DECIMALS
                        round all floating point numbers to this number of decimal places prior to comparison
```

## Things to do

- prepare and release PyPI package
- add unit tests

## Contributing

It is currently good enough for me so I don't intend to spend much more time on it.
You are welcome to implement stuff from `Things to do` or more and submit pull requests.

## Change Log

- 0.9.0-1 Implements mixed sorting (numerical sort first, alphanumerical string sort next)
- 0.9.0 The first complete port of json-diff JS library with all the functionality

## Credits

- [json-diff](https://github.com/andreyvit/json-diff)

Released under the MIT license.

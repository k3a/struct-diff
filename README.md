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

and from that it can generate a human-readable structural diff:

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

## Things to do

- prepare and release PyPI package
- add unit tests

## Contributing

It is currently good enough for me so I don't intend to spend much more time on it.
You are welcome to implement stuff from `Things to do` or more and submit pull requests.

## Change Log

- 0.9.0 The first complete port of json-diff JS library with all the functionality

## Credits

- [json-diff](https://github.com/andreyvit/json-diff)

Released under the MIT license.

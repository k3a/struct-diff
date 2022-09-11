# struct_diff

Copares two objects and produces a dict describing changes.
Ideal for comparing two JSON or YAML objects and generating a structural diff.

## Purpose

It produces changedict like this:

```json
{
    "__type": "object",
    "__remove": {
        "type": "donut"
    },
    "__update": {
        "arr": {
            "__type": "array",
            "__append": {
                "3": 4
            },
            "__update": {
                "1": {
                    "obj": "ok",
                    "secondkey": 123
                }
            },
            "__original": {
                "__length": 3,
                "1": 2
            }
        },
        "name": "Donut",
        "thumbnail": {
            "__type": "object",
            "__append": {
                "extra": {
                    "price": 111,
                    "sizes": [
                        "L",
                        "XL"
                    ]
                }
            },
            "__update": {
                "width": 64
            },
            "__original": {
                "width": 32
            }
        },
        "image": {
            "__type": "object",
            "__update": {
                "caption": {
                    "__type": "object",
                    "__update": {
                        "width": 321,
                        "height": {
                            "value": 642,
                            "units": "mm"
                        }
                    },
                    "__original": {
                        "width": 123,
                        "height": 321
                    }
                }
            },
            "__original": {
                "caption": {
                    "text": "image",
                    "width": 123,
                    "height": 321
                }
            }
        }
    },
    "__original": {
        "arr": [
            1,
            2,
            3
        ],
        "name": "Cake",
        "thumbnail": {
            "url": "images/thumbnails/0001.jpg",
            "width": 32,
            "height": 32
        },
        "image": {
            "url": "images/0001.jpg",
            "width": 200,
            "caption": {
                "text": "image",
                "width": 123,
                "height": 321
            },
            "height": 200
        }
    }
}
```

and it is also able to generate a YAML representation of changes `./struct_diff.py testdata/j*.json -Y`:

```yaml
-type: donut
 arr:
  ...
- - 2
+ - 2
  ...
+ - 4
 image:
  caption:
-  height: 321
+  height: 
+   units: mm
+   value: 642
-  width: 123
+  width: 321
-name: Cake
+name: Donut
 thumbnail:
+ extra: 
+  price: 111
+  sizes:
+  - L
+  - XL
- width: 32
+ width: 64
```

## Things to do

- add unit tests
- create a JSON formatter similar to [json-diff](https://github.com/andreyvit/json-diff) JS library
- add a new formatter or extend existing ones to generate colored CLI output

## Contributing

It is currently good enough for me so I don't intend to spend much more time on it.
You are welcome to implement stuff from `Things to do` or more and submit pull requests.

## Credits

Based on unmaintained [json_diff](https://gitlab.com/mcepl/json_diff/-/tree/master/) MIT python code.
I probably wouldn't bother writing it all from scratch so thanks for the original work.
And because the original work was MIT, I am releasing my additions here as MIT as well. :)

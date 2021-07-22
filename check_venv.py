import sys

if getattr(sys, "real_prefix", None) is not None:
    print("Maybe in a virtualenv")
else:
    print("Probably not in a virtualenv")
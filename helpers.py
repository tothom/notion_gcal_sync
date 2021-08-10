from types import SimpleNamespace

def nested_simple_namespace(d):
    simple_namespace = SimpleNamespace()
    for k, v in d.items():
        if isinstance(v, dict):
            setattr(simple_namespace, k, nested_simple_namespace(v))
        else:
            setattr(simple_namespace, k, v)
    return simple_namespace

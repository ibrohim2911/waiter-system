import importlib, os
try:
    mod = importlib.import_module('rest_framework_simplejwt.token_blacklist')
    path = os.path.dirname(mod.__file__)
    print('module_path:', path)
    print('contains:', os.listdir(path))
    mgmt_path = os.path.join(path, 'management', 'commands')
    print('management.commands exists:', os.path.isdir(mgmt_path))
    models_mod = importlib.import_module('rest_framework_simplejwt.token_blacklist.models')
    print('models:', [n for n in dir(models_mod) if not n.startswith('_')])
except Exception as e:
    print('error:', e)

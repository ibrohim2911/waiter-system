import importlib, os
try:
    mod = importlib.import_module('rest_framework_simplejwt.token_blacklist')
    path = os.path.dirname(mod.__file__)
    mgmt_path = os.path.join(path, 'management', 'commands')
    if os.path.isdir(mgmt_path):
        print('management.commands files:', os.listdir(mgmt_path))
    else:
        print('no management.commands')
    print('token_blacklist package path:', path)
    print('package contains:', os.listdir(path))
except Exception as e:
    print('error:', e)

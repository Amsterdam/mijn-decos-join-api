import os


def check_env():
    """
    Checks if all required environment variables have been set
    """
    missing_vars = [v for v in []
                    if not os.getenv(v, None)]
    if missing_vars:
        raise Exception('Missing environment variables {}'.format(', '.join(missing_vars)))

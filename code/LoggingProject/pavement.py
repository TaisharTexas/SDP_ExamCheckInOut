from paver.easy import task
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname('LoggingProject')))

@task
def test():
    """Run Django unit tests."""
    os.environ['DJANGO_SETTINGS_MODULE'] = 'LoggingProject.settings'  
   
    from django.core.management import execute_from_command_line
    execute_from_command_line([sys.argv[0], 'test'])

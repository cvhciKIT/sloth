from sloth.core.cli import BaseCommand, CommandError
from sloth.annotations.container import *
from optparse import make_option, OptionParser
import shutil

class ConvertCommand(BaseCommand):
    """
    Converts a label file from one file format to another.
    """
    args = '<input> <output>'
    help = __doc__.strip()

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("Expect exactly 2 arguments.")

        raise CommandError("Not implemented")


class CreateConfigCommand(BaseCommand):
    """
    Creates a configuration file with default values.
    """
    args = '<output>'
    help = __doc__.strip()
    option_list = BaseCommand.option_list + (
        make_option('-f', '--force', action='store_true', default=False,
            help='Overwrite the file if it exists.'),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Expect exactly 1 argument.")

        template_dir = os.path.join(sloth.__path__[0], 'conf', 'template')
        config_template = os.path.join(template_dir, 'config_template.py')
        target = args[0]

        if os.path.exists(target) and not options['force']:
            sys.stderr.write("Error: %s exists.  Use -f to overwrite.\n" % target)
            return

        try:
            shutil.copy(config_template, target)
            _make_writeable(target)
        except OSError, e:
            sys.stderr.write("Notice: Couldn't set permission bits on %s.\n" % target)


class DumpLabelsCommand(BaseCommand):
    """
    Dumps the labels from a label file to stdout.
    """
    args = '<labelfile>'
    help = __doc__.strip()

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Expect exactly 1 argument.")

        raise CommandError("Not implemented")


class AppendFilesCommand(BaseCommand):
    """
    Append image or video files to a label file.  Creates the label
    file if it does not exist before.
    """
    args = '<labelfile> <file1> [<file2> ...]'
    help = __doc__.strip()

    def handle(self, *args, **options):
        if len(args) < 2:
            raise CommandError("Expect at least 2 arguments.")

        raise CommandError("Not implemented")


def _make_writeable(filename):
    """
    Make sure that the file is writeable. Useful if our source is
    read-only.
    """
    import stat
    if sys.platform.startswith('java'):
        # On Jython there is no os.access()
        return
    if not os.access(filename, os.W_OK):
        st = os.stat(filename)
        new_permissions = stat.S_IMODE(st.st_mode) | stat.S_IWUSR
        os.chmod(filename, new_permissions)

# command dictionary str -> Command
_commands = {}

def register_command(name, command):
    global _commands
    _commands[name] = command

def get_commands():
    global _commands
    return _commands

# TODO automatically discover these
register_command('convert', ConvertCommand())
register_command('createconfig', CreateConfigCommand())
register_command('dumplabels', DumpLabelsCommand())
register_command('appendfiles', AppendFilesCommand())

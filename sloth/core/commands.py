import sys
import os
import sloth
import shutil
from pprint import pprint
from sloth.core.cli import BaseCommand, CommandError
from sloth.annotations.container import *
from optparse import make_option
import logging
logger = logging.getLogger(__name__)

class ConvertCommand(BaseCommand):
    """
    Converts a label file from one file format to another.
    """
    args = '<input> <output>'
    help = __doc__.strip()

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("convert: Expecting exactly 2 arguments.")

        input, output = args[:]
        logger.info("converting from %s to %s" % (input, output))

        logger.debug("loading annotations from %s" % input)
        self.labeltool.loadAnnotations(input)

        logger.debug("saving annotations to %s" % output)
        self.labeltool.saveAnnotations(output)


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

        template_dir = os.path.join(sloth.__path__[0], 'conf')
        config_template = os.path.join(template_dir, 'default_config.py')
        target = args[0]

        if os.path.exists(target) and not options['force']:
            sys.stderr.write("Error: %s exists.  Use -f to overwrite.\n" % target)
            return

        try:
            shutil.copy(config_template, target)
            _make_writeable(target)
        except OSError as e:
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

        self.labeltool.loadAnnotations(args[0])
        pprint(self.labeltool.annotations())


class AppendFilesCommand(BaseCommand):
    """
    Append image or video files to a label file.  Creates the label
    file if it does not exist before.
    """
    args = '<labelfile> <file1> [<file2> ...]'
    help = __doc__.strip()
    option_list = BaseCommand.option_list + (
        make_option('-u', '--unlabeled', action='store_true', default=False,
            help='Mark appended files as unlabeled.'),
        make_option(      '--image', action='store_true', default=False,
            help='Force appended files to be recognized as images.'),
        make_option(      '--video', action='store_true', default=False,
            help='Force appended files to be recognized as videos.'),
    )

    video_extensions = ['.vob', '.idx', '.mpg', '.mpeg']

    def handle(self, *args, **options):
        if len(args) < 2:
            raise CommandError("Expect at least 2 arguments.")

        self.labeltool.loadAnnotations(args[0])
        for filename in args[1:]:
            rel_filename = filename
            try:
                if not os.path.isabs(filename):
                    rel_filename = os.path.relpath(filename, os.path.dirname(args[0]))
            except:
                pass

            _, ext = os.path.splitext(rel_filename)
            if (not options['image'] and ext.lower() in self.video_extensions) or options['video']:
                logger.debug("Adding video file: %s" % rel_filename)
                item = self.labeltool.addVideoFile(rel_filename)
            else:
                logger.debug("Adding image file: %s" % rel_filename)
                item = self.labeltool.addImageFile(rel_filename)

            if options['unlabeled']:
                item.setUnlabeled(True)
        self.labeltool.saveAnnotations(args[0])


class MergeFilesCommand(BaseCommand):
    """
    Merge annotations of two label files and create a new one from it.
    Currently, only video annotation files are supported.
    If both input files have annotations for the same frame number, the result
    will contain the union of both annotations.
    
    Output format will be determined by the file suffix of output.
    """
    args = '<labelfile 1> <labelfile 2> <output>'
    help = __doc__.strip()

    def handle(self, *args, **options):
        if len(args) != 3:
            raise CommandError("Usage: %s" % self.args)

        input1, input2, output = args[:]
        logger.info("merging %s and %s into %s" % (input1, input2, output))
        logger.debug("loading annotations from %s" % input1)
        container1 = self.labeltool._container_factory.create(input1)
        an1 = container1.load(input1)

        logger.debug("loading annotations from %s" % input2)
        container2 = self.labeltool._container_factory.create(input2)
        an2 = container2.load(input2)

        logger.debug("merging annotations of %s and %s" % (input1, input2))
        an3 = self.merge_annotations(an1, an2)

        logger.debug("saving annotations to %s" % output)
        containerOut = self.labeltool._container_factory.create(output)
        containerOut.save(an3, output)

    
    def merge_annotations(self, an1, an2):
    
        # I could also think of an implementation merging an1 and an2, and flattening the lists of lists
        # that are obtained
        assert(len(an1) == 1 and len(an2) == 1)
        d1 = an1[0]
        d2 = an2[0]
        
        if(d1['class'] != 'video'):
            raise NotImplemented('mergefiles: Currently, only annotation files from video can be merged.')
            
        if(d2['class'] != d1['class']):
            raise CommandError("mergefiles: Both annotation files have to be of the same type (%s vs. %s)." % (d1['class'], d2['class']))
        
        if(d1['filename'] != d2['filename']):
            raise CommandError('mergefiles: Both annotation files must annotate the same video file.')

        assert(d1['frames'] != None)
        assert(d2['frames'] != None)
        
        
        frames1 = d1['frames']
        frames2 = d2['frames']
        
        # collect list of nums
        frameNums1 = set()
        for frame in frames1:
            frameNums1.add(frame['num']) 
            
        # make frames2 accessible by frame number
        frameNums2 = dict()
        for frame in frames2:
            frameNums2[frame['num']] = frame
        
        for frame in frames1:
            num = frame['num']
            # look for frame with same timestamp in frames2
            if num in frameNums2:
                # update annotations
                frame['annotations'].extend(frameNums2[num]['annotations'])
        
        # append frames with nums only in frames2 to frames1        
        numsOnlyIn2 = set(frameNums2.keys()) - frameNums1
        for key in numsOnlyIn2:
            frames1.append(frameNums2[key])
        
        from operator import itemgetter
        frames1.sort(key=itemgetter('num'))        
        
        return an1


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
register_command('mergefiles', MergeFilesCommand())

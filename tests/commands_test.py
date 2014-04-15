from sloth.core.commands import *


def test_merge_command_same_images():
    ann1 = [{'class': 'image', 'filename': 'abc.jpg',
             'annotations': []},
            {'class': 'image', 'filename': 'def.jpg',
             'annotations': [
                 {'class': 'point', 'x': 10, 'y': 100}
             ]}]
    ann2 = [{'class': 'image', 'filename': 'abc.jpg',
             'annotations': []},
            {'class': 'image', 'filename': 'def.jpg',
             'custom': 1,
             'annotations': [
                {'class': 'point', 'x': 10, 'y': 100}
             ]}]

    mc = MergeFilesCommand()
    ann3 = mc.merge_annotations(ann1, ann2)
    assert len(ann3) == 2
    assert ann3[1].get('custom') == 1


def test_merge_command_different_images():
    ann1 = [{'class': 'image', 'filename': 'abc.jpg',
             'annotations': []},
            {'class': 'image', 'filename': 'def.jpg',
             'annotations': [
                 {'class': 'point', 'x': 10, 'y': 100}
             ]}]
    ann2 = [{'class': 'image', 'filename': 'abc1.jpg',
             'annotations': []},
            {'class': 'image', 'filename': 'def2.jpg',
             'annotations': [
                {'class': 'point', 'x': 10, 'y': 100}
             ]}]

    mc = MergeFilesCommand()
    ann3 = mc.merge_annotations(ann1, ann2)
    assert len(ann3) == 4


def test_merge_command_empty():
    ann1 = []
    ann2 = [{'class': 'image', 'filename': 'abc1.jpg',
             'annotations': []},
            {'class': 'image', 'filename': 'def2.jpg',
             'annotations': [
                {'class': 'point', 'x': 10, 'y': 100}
             ]}]

    mc = MergeFilesCommand()
    ann3 = mc.merge_annotations(ann1, ann2)
    assert len(ann3) == 2


def test_merge_command_different_same_videos():
    ann1 = [{'class': 'image', 'filename': 'abc.jpg',
             'annotations': []},
            {'class': 'video', 'filename': 'def.avi',
             'frames': [
                 {'class': 'frame', 'num': 10, 'timestamp': 100.0,
                  'annotations': [
                    {'class': 'point', 'x': 10, 'y': 100}
                  ]},
                 {'class': 'frame', 'num': 12, 'timestamp': 102.0,
                  'annotations': [
                    {'class': 'point', 'x': 10, 'y': 100}
                  ]}
             ]}]
    ann2 = [{'class': 'video', 'filename': 'def.avi',
             'frames': [
                 {'class': 'frame', 'num': 10, 'timestamp': 100.0,
                  'annotations': [
                    {'class': 'point', 'x': 10, 'y': 100}
                  ]},
                 {'class': 'frame', 'num': 11, 'timestamp': 101.0,
                  'annotations': [
                    {'class': 'point', 'x': 10, 'y': 100}
                  ]}]
            },
            {'class': 'image', 'filename': 'def2.jpg',
             'annotations': [
                {'class': 'point', 'x': 10, 'y': 100}
             ]}]

    mc = MergeFilesCommand()
    ann3 = mc.merge_annotations(ann1, ann2)
    assert len(ann3) == 3

    item = [it for it in ann3 if it['filename'] == 'def.avi'][0]
    assert len(item['frames']) == 3
    assert item['frames'][0]['num'] == 10
    assert item['frames'][1]['num'] == 11
    assert item['frames'][2]['num'] == 12
    assert len(item['frames'][0]['annotations']) == 2


def test_merge_command_same_file(tmpdir):
    class LabelToolMockup:
        container_config = (('*', 'sloth.annotations.container.JsonContainer'),)
        _container_factory = AnnotationContainerFactory(container_config)

    mc = MergeFilesCommand()
    mc.labeltool = LabelToolMockup()
    output_fname = str(tmpdir.join('output.json'))
    mc.handle('tests/data/example1_labels.json', 'tests/data/example1_labels.json', output_fname)

    import json
    merged_annotations = json.load(open(output_fname))
    assert len(merged_annotations) == 2
    assert len(merged_annotations[0]['annotations']) == 4
    assert len(merged_annotations[1]['annotations']) == 2

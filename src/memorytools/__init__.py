import gc
import locale
import os
import sys

locale.setlocale(locale.LC_ALL, 'en_US')
fmt = lambda stat: locale.format('%d', stat, grouping=True)


def save_objects(objs=None):
  """
    Save gc.get_objects() to /var/tmp/objects-$pid with summary on top,
    from `summarize_objects`.

    Each object is converted to str and saved in descending order by size. I.e.::

      IDX 3648: 12568 <type 'dict'> {'REPEAT_ONE': 'repeat_one', 'makedict': <function makedict ...

    The above means array index 3648, 12568 bytes, data type dict, and data content as str.
    Easily go to the next record by searching for 'IDX '.

    :param list objs: gc objects to summarize. Defaults to gc.get_objects()
  """
  objs = objs or gc.get_objects()

  objs_sizes = sorted([(sys.getsizeof(o), i) for i, o in enumerate(objs)], reverse=True)
  objs_size = sum([s[0] for s in objs_sizes])
  objs_file = '/var/tmp/objects-%s' % os.getpid()

  with open(objs_file, 'w') as fp:
    fp.write('Objects count: %s\n' % fmt(len(objs)))
    fp.write('Objects size: %s\n\n' % fmt(objs_size))

    fp.write('Objects summary:\n%s\n\n' % summarize_objects(objs, echo=False))

    for size, i in objs_sizes:
      try:
        fp.write('IDX %d: %d %s %s\n' % (i, size, type(objs[i]), str(objs[i])))
      except Exception as e:
        fp.write('IDX %d: %d %s EXCEPTION: %s\n' % (i, size, type(objs[i]), str(e)))

  msg = 'Wrote %d objects to %s (%d bytes)' % (len(objs), objs_file, objs_size)
  print msg

  return msg


def summarize_objects(objs=None, echo=True):
  """
    Provide a summary of gc objects based on type. Two summaries: ordered by size, ordered by count

    :param list objs: gc objects to summarize. Defaults to gc.get_objects()
    :param bool echo: Print summary results to stdout if True, otherwise return results instead.
    :return: Summary results if echo is False
  """
  if not objs:
    objs = gc.get_objects()

  objs_dict = _summarize_objects(objs)
  size_summary = ['{0:>10s} {1:>5s} {2}'.format('Size', 'Count', 'Type')]
  count_summary = ['{0:>5s} {1:>10s} {2}'.format('Count', 'Size', 'Type')]
  objs_by_size = []
  objs_by_count = []

  total_size = total_count = 0

  for kind, stats in objs_dict.iteritems():
    objs_by_size.append((stats['size'], stats['count'], kind))
    objs_by_count.append((stats['count'], stats['size'], kind))
    total_size += stats['size']
    total_count += stats['count']

  for size, count, kind in sorted(objs_by_size, reverse=True):
    size_summary.append('{0:>10s} {1:>5s} {2}'.format(fmt(size), fmt(count), kind))

  for count, size, kind in sorted(objs_by_count, reverse=True):
    count_summary.append('{0:>5s} {1:>10s} {2}'.format(fmt(count), fmt(size), kind))

  if echo:
    print 'Objects count', fmt(total_count)
    print 'Objects size', fmt(total_size)
    print

    for summary in [size_summary, count_summary]:
      print '\n'.join(summary[:10])
      if len(summary) > 10:
        print '... %d more' % (len(summary) - 10)
      print

  else:
    return '\n'.join(size_summary + [''] + count_summary)


def _summarize_objects(objs):
  objs_dict = {}

  for obj in objs:
    _incr(objs_dict, type(obj), 'count')
    _incr(objs_dict, type(obj), 'size', sys.getsizeof(obj))

  return objs_dict


def _incr(objs_dict, kind, stat, value=1):
  if kind not in objs_dict:
    objs_dict[kind] = {}

  if stat not in objs_dict[kind]:
    objs_dict[kind][stat] = value
  else:
    objs_dict[kind][stat] += value

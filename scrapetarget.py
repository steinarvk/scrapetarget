import flask
import time
import random
import loremipsum
import ast
import sys
import argparse

def generate_base_content(size):
  n = random.randint(size, size*2)
  return "\n\n".join(loremipsum.get_paragraphs(n))

def generate_content(size, include_needle=False, needle_pattern="needle"):
  content = generate_base_content(size)
  if not include_needle:
    content = content.replace(needle_pattern, "")
  else:
    index = random.randint(0, len(content))
    content = content[:index] + needle_pattern + content[index:]
  return content

class Uptimer(object):
  def __init__(self):
    self.t0 = time.time()

  def uptime(self):
    return time.time() - self.t0

app = flask.Flask(__name__)
_timer = Uptimer()

@app.route("/")
def page():
  # Phase (in seconds) of off/on cycle
  phase = flask.request.args.get("phase", default=0, type=int)
  # Length (in seconds) of off-part of the cycle
  off_period = flask.request.args.get("off_period", default=300, type=int)
  # Length (in seconds) of on-part of the cycle
  on_period = flask.request.args.get("on_period", default=300, type=int)
  # Length (in seconds) of entire cycle. Specify only without off/on_period
  period = flask.request.args.get("period", type=int)
  if (period and
      not any(flask.request.args.get(k) for k in ("on_period", "off_period"))):
    off_period = on_period = float(period) / 2.0
  # Error mode: 404 never, always, or when_off
  error_mode = flask.request.args.get("error_mode", default="never")
  # Size of generated content
  size = flask.request.args.get("size", default=10, type=int)
  # Pattern to hide in the "on" content
  pattern = flask.request.args.get("pattern", default="needle")
  # Pattern to hide in the "on" content
  useragent = flask.request.args.get("require_useragent")
  # Include a debugging suffix on the page?
  debug_suffix = flask.request.args.get("debug_suffix")
  # Generate content instead of an error message even when serving 404?
  content_on_error = flask.request.args.get("content_on_error")

  if useragent and useragent != flask.request.headers.get("User-Agent"):
    return "Forbidden", 403

  t = _timer.uptime()
  full_period = on_period + off_period
  t_modulo = (t + phase) % full_period
  on = t_modulo > off_period
  content = generate_content(size, include_needle=on, needle_pattern=pattern)
  if error_mode == "never":
    error = False
  elif error_mode == "always":
    error = True
  else:
    assert error_mode == "when_off"
    error = not on
  if error and not content_on_error:
    content = "404 Not Found"
  if debug_suffix:
    content += "\n" + repr((on, t_modulo, off_period, full_period))
  return_code = 404 if error else 200

  return content, return_code

if __name__ == '__main__':
  desc = "Web server to serve as target for a programming exercise"
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument("--debug", action="store_true", default=False)
  parser.add_argument("--public", action="store_true", default=False)
  parser.add_argument("--port", default=5000, type=int)
  args = parser.parse_args()
  host = None
  if args.debug:
    app.debug = True
  if args.public:
    if args.debug:
      print >>sys.stderr, """\
Cannot run in debug mode and listen publicly.
(Flask allows arbitrary remote code execution in debug mode!)
"""
      sys.exit(1)
    else:
      host = "0.0.0.0"
  app.run(host=host, port=args.port)

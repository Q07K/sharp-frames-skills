"""Execute a candidate's unittest suite and preserve counts without treating skips as passes."""
from pathlib import Path
import json
import sys
import unittest

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
suite = unittest.defaultTestLoader.discover(str(root / 'tests'))
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'collected': result.testsRun, 'failures': len(result.failures),
                  'errors': len(result.errors), 'skipped': len(result.skipped),
                  'expected_failures': len(result.expectedFailures),
                  'unexpected_successes': len(result.unexpectedSuccesses),
                  'successful': result.wasSuccessful()}))
raise SystemExit(0 if result.wasSuccessful() else 1)

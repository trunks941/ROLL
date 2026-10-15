#!/usr/bin/env python3
"""Ensure native compiler proof cannot follow changed or incomplete sources."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import generate as gen


def main():
    digest = 'a' * 64
    valid = dict(project='ROLL_fixture', sourceSHA256=digest,
                 sourceGenerationSucceeded=True, sourceInventoryComplete=True,
                 plcCompilation=dict(state='Warning', errorCount=0, warningCount=1),
                 retentionConfigured=True, hmiFullyConfigured=False,
                 physicalIoConfigured=False)
    cases = [
        ('matching', {}, True),
        ('different_source', {'sourceSHA256': 'b' * 64}, False),
        ('compile_error', {'plcCompilation': dict(state='Error', errorCount=1, warningCount=0)}, False),
        ('incomplete', {'sourceInventoryComplete': False}, False),
        ('generation_failed', {'sourceGenerationSucceeded': False}, False),
    ]
    with tempfile.TemporaryDirectory(prefix='roll-native-evidence-') as directory:
        root = Path(directory)
        (root / 'reports').mkdir()
        path = root / 'reports/windows-feedback-fixture.json'
        with patch.object(gen, 'OUT', root):
            for name, changes, expected in cases:
                path.write_text(json.dumps(dict(valid, **changes)))
                result = gen.matching_native_feedback(digest)
                assert (result is not None) == expected, name
                if result:
                    assert result['source_sha256'] == digest and result['plc_errors'] == 0
    print(f'Native compiler evidence: {len(cases)} source/result matching scenarios passed; TIA was not executed.')


if __name__ == '__main__':
    main()

---
name: Bug report
about: Create a report to help us improve
title: ''
labels: bug
assignees: ''

---

## Bug Description
A clear and concise description of what the bug is.

## Reproduction Steps
Steps to reproduce the behavior:
1. Define dataclass with '...'
2. Call build_config with '...'
3. Run command '...'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
A clear and concise description of what actually happened.

## Minimal Example
```python
from dataclasses import dataclass
from dataclass_args import build_config

@dataclass
class Config:
    # Your minimal reproduction case here
    pass

# Code that demonstrates the issue
config = build_config(Config)
```

## Environment
- Python version: [e.g. 3.10.0]
- dataclass-args version: [e.g. 1.0.0]
- Operating System: [e.g. Ubuntu 22.04, Windows 11, macOS 13.0]
- Command used: [e.g. `python app.py --name test`]

## Error Message
If applicable, paste the full error message and stack trace:

```
Error traceback here
```

## Additional Context
Add any other context about the problem here.
